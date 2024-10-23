from __future__ import annotations

from decimal import Decimal

from mm_std import ConcurrentTasks, Result
from pydantic import BaseModel
from rich.progress import TaskID

from mm_balance import output
from mm_balance.config import Config
from mm_balance.constants import NETWORK_APTOS, NETWORK_BITCOIN, NETWORK_SOLANA, Network
from mm_balance.rpc import aptos, btc, evm, solana
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
        self.tasks: dict[Network, list[Balances.Balance]] = {network: [] for network in config.networks()}
        self.progress_bar = output.create_progress_bar()
        self.progress_bar_task: dict[Network, TaskID] = {}

        for idx, group in enumerate(config.groups):
            task_list = [Balances.Balance(group_index=idx, address=a, token_address=group.token_address) for a in group.addresses]
            self.tasks[group.network].extend(task_list)

        for network in config.networks():
            if self.tasks[network]:
                self.progress_bar_task[network] = output.create_progress_task(
                    self.progress_bar, network, len(self.tasks[network])
                )

    def process(self) -> None:
        with self.progress_bar:
            job = ConcurrentTasks(max_workers=10)
            for network in self.config.networks():
                job.add_task(network, self._process_network, args=(network,))
            job.execute()

    def _process_network(self, network: Network) -> None:
        job = ConcurrentTasks(max_workers=self.config.workers[network])
        for idx, task in enumerate(self.tasks[network]):
            job.add_task(str(idx), self._get_balance, args=(network, task.address, task.token_address))
        job.execute()
        # TODO: print job.exceptions if present
        for idx, _task in enumerate(self.tasks[network]):
            self.tasks[network][idx].balance = job.result.get(str(idx))  # type: ignore[assignment]

    def _get_balance(self, network: Network, wallet_address: str, token_address: str | None) -> Result[Decimal]:
        nodes = self.config.nodes[network]
        round_ndigits = self.config.round_ndigits
        proxies = self.config.proxies
        token_decimals = self.token_decimals[network][token_address]

        if network.is_evm_network():
            res = evm.get_balance(nodes, wallet_address, token_address, token_decimals, proxies, round_ndigits)
        elif network == NETWORK_BITCOIN:
            res = btc.get_balance(wallet_address, proxies, round_ndigits)
        elif network == NETWORK_APTOS:
            res = aptos.get_balance(nodes, wallet_address, token_address, token_decimals, proxies, round_ndigits)
        elif network == NETWORK_SOLANA:
            res = solana.get_balance(nodes, wallet_address, token_address, token_decimals, proxies, round_ndigits)
        else:
            raise ValueError(f"Unsupported network: {network}")

        self.progress_bar.update(self.progress_bar_task[network], advance=1)
        return res

    def get_group_balances(self, group_index: int, network: Network) -> list[Balance]:
        # TODO: can we get network by group_index?
        return [b for b in self.tasks[network] if b.group_index == group_index]

    def get_errors(self) -> list[Balance]:
        result = []
        for network in self.tasks:
            for task in self.tasks[network]:
                if task.balance is not None and task.balance.is_err():
                    result.append(task)
        return result
