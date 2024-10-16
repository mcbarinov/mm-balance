from __future__ import annotations

from decimal import Decimal

from mm_std import ConcurrentTasks, Result
from pydantic import BaseModel
from rich.progress import TaskID

from mm_balance import output
from mm_balance.config import Config
from mm_balance.constants import Network
from mm_balance.rpc import btc, eth, solana
from mm_balance.token_decimals import TokenDecimals


class Balances:
    class Balance(BaseModel):
        group_index: int
        address: str
        token_address: str | None
        balance: Result[Decimal] | None = None

    def __init__(self, config: Config, token_decimals: TokenDecimals):
        self.config = config
        self.token_decimals = token_decimals
        self.tasks: dict[Network, list[Balances.Balance]] = {network: [] for network in Network}
        self.progress_bar = output.create_progress_bar()
        self.progress_bar_task: dict[Network, TaskID] = {}

        for idx, group in enumerate(config.groups):
            task_list = [Balances.Balance(group_index=idx, address=a, token_address=group.token_address) for a in group.addresses]
            self.tasks[group.network].extend(task_list)

        for network in Network:
            if self.tasks[network]:
                self.progress_bar_task[network] = output.create_progress_task(
                    self.progress_bar, network.value, len(self.tasks[network])
                )

    def process(self) -> None:
        with self.progress_bar:
            job = ConcurrentTasks(max_workers=10)
            for network in Network:
                job.add_task(network.value, self._process_network, args=(network,))
            job.execute()

    def _process_network(self, network: Network) -> None:
        job = ConcurrentTasks(max_workers=self.config.workers[network])
        for idx, task in enumerate(self.tasks[network]):
            job.add_task(str(idx), self._get_balance, args=(network, task.address, task.token_address))
        job.execute()
        for idx, _task in enumerate(self.tasks[network]):
            self.tasks[network][idx].balance = job.result.get(str(idx))  # type: ignore[assignment]

    def _get_balance(self, network: Network, wallet_address: str, token_address: str | None) -> Result[Decimal]:
        nodes = self.config.nodes[network]
        round_ndigits = self.config.round_ndigits
        proxies = self.config.proxies
        token_decimals = self.token_decimals[network][token_address] if token_address else -1
        match network:
            case Network.BITCOIN:
                res = btc.get_balance(wallet_address, proxies, round_ndigits)
            case Network.ETHEREUM | Network.ARBITRUM_ONE | Network.OP_MAINNET:
                if token_address is None:
                    res = eth.get_native_balance(nodes, wallet_address, proxies, round_ndigits)
                else:
                    res = eth.get_token_balance(nodes, wallet_address, token_address, token_decimals, proxies, round_ndigits)
            case Network.SOLANA:
                if token_address is None:
                    res = solana.get_native_balance(nodes, wallet_address, proxies, round_ndigits)
                else:
                    res = solana.get_token_balance(nodes, wallet_address, token_address, token_decimals, proxies, round_ndigits)

            case _:
                raise ValueError

        self.progress_bar.update(self.progress_bar_task[network], advance=1)
        return res

    def get_group_balances(self, group_index: int, network: Network) -> list[Balance]:
        # TODO: can we get network by group_index?
        return [b for b in self.tasks[network] if b.group_index == group_index]
