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
            case Network.BTC:
                res = btc.get_balance(wallet_address, proxies, round_ndigits)
            case Network.ETH:
                if token_address is None:
                    res = eth.get_native_balance(nodes, wallet_address, proxies, round_ndigits)
                else:
                    res = eth.get_token_balance(nodes, wallet_address, token_address, token_decimals, proxies, round_ndigits)
            case Network.SOL:
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


# class Balances2(BaseModel):
#     class Balance(BaseModel):
#         group_index: int
#         address: str
#         token_address: str | None
#         balance: Result[Decimal] | None = None
#
#     config: Config
#     token_decimals: TokenDecimals
#     # separate balance tasks on networks
#     btc: list[Balance]
#     eth: list[Balance]
#     sol: list[Balance]
#
#     def network_tasks(self, network: Network) -> list[Balance]:
#         if network == Network.BTC:
#             return self.btc
#         elif network == Network.ETH:
#             return self.eth
#         elif network == Network.SOL:
#             return self.sol
#         else:
#             raise ValueError
#
#     def get_group_balances(self, group_index: int, network: Network) -> list[Balance]:
#         # TODO: can we get network by group_index?
#         if network == Network.BTC:
#             network_balances = self.btc
#         elif network == Network.ETH:
#             network_balances = self.eth
#         elif network == Network.SOL:
#             network_balances = self.sol
#         else:
#             raise ValueError
#
#         return [b for b in network_balances if b.group_index == group_index]
#
#     def process(self) -> None:
#         progress = output.create_progress_bar()
#         task_btc = output.create_progress_task(progress, "btc", len(self.btc))
#         task_eth = output.create_progress_task(progress, "eth", len(self.eth))
#         task_sol = output.create_progress_task(progress, "sol", len(self.sol))
#         with progress:
#             job = ConcurrentTasks()
#             job.add_task("btc", self._process_btc, args=(progress, task_btc))
#             job.add_task("eth", self._process_eth, args=(progress, task_eth))
#             job.add_task("sol", self._process_sol, args=(progress, task_sol))
#             job.execute()
#
#     def _process_btc(self, progress: Progress, task_id: TaskID) -> None:
#         job = ConcurrentTasks(max_workers=self.config.workers.btc)
#         for idx, task in enumerate(self.btc):
#             job.add_task(str(idx), btc.get_balance, args=(task.address, self.config, progress, task_id))
#         job.execute()
#         for idx, _task in enumerate(self.btc):
#             self.btc[idx].balance = job.result.get(str(idx))  # type: ignore[assignment]
#
#     def _process_eth(self, progress: Progress, task_id: TaskID) -> None:
#         job = ConcurrentTasks(max_workers=self.config.workers.eth)
#         for idx, task in enumerate(self.eth):
#             job.add_task(str(idx), self._get_balance,
#                          args=(Network.ETH, task.address, task.token_address, self.config, progress, task_id))
#         job.execute()
#         for idx, _task in enumerate(self.eth):
#             self.eth[idx].balance = job.result.get(str(idx))  # type: ignore[assignment]
#
#     def _process_sol(self, progress: Progress, task_id: TaskID) -> None:
#         job = ConcurrentTasks(max_workers=self.config.workers.sol)
#         for idx, task in enumerate(self.sol):
#             job.add_task(str(idx), solana.get_balance, args=(task.address, self.config, progress, task_id))
#         job.execute()
#         for idx, _task in enumerate(self.sol):
#             self.sol[idx].balance = job.result.get(str(idx))  # type: ignore[assignment]
#
#     @staticmethod
#     def from_config(config: Config, token_decimals: TokenDecimals) -> Balances:
#         tasks = Balances(config=config, btc=[], eth=[], sol=[], token_decimals=token_decimals)
#         for idx, group in enumerate(config.groups):
#             task_list = [Balances.Balance(group_index=idx, address=a, token_address=group.token_address) for a in group.addresses] # noqa
#             if group.network == Network.BTC:
#                 tasks.btc.extend(task_list)
#             elif group.network == Network.ETH:
#                 tasks.eth.extend(task_list)
#             elif group.network == Network.SOL:
#                 tasks.sol.extend(task_list)
#         return tasks
