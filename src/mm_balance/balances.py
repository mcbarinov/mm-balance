from __future__ import annotations

from decimal import Decimal

from mm_std import ConcurrentTasks, Result
from pydantic import BaseModel
from rich.progress import Progress, TaskID

from mm_balance import output
from mm_balance.config import Config
from mm_balance.rpc import btc, eth, solana
from mm_balance.types import Network


class Balances(BaseModel):
    class Balance(BaseModel):
        group_index: int
        address: str
        token_address: str | None
        balance: Result[Decimal] | None = None

    config: Config
    # separate balance tasks on networks
    btc: list[Balance]
    eth: list[Balance]
    sol: list[Balance]

    def network_tasks(self, network: Network) -> list[Balance]:
        if network == Network.BTC:
            return self.btc
        elif network == Network.ETH:
            return self.eth
        elif network == Network.SOL:
            return self.sol
        else:
            raise ValueError

    def get_group_balances(self, group_index: int, network: Network) -> list[Balance]:
        # TODO: can we get network by group_index?
        if network == Network.BTC:
            network_balances = self.btc
        elif network == Network.ETH:
            network_balances = self.eth
        elif network == Network.SOL:
            network_balances = self.sol
        else:
            raise ValueError

        return [b for b in network_balances if b.group_index == group_index]

    def process(self) -> None:
        progress = output.create_progress_bar()
        task_btc = output.create_progress_task(progress, "btc", len(self.btc))
        task_eth = output.create_progress_task(progress, "eth", len(self.eth))
        task_sol = output.create_progress_task(progress, "sol", len(self.sol))
        with progress:
            job = ConcurrentTasks()
            job.add_task("btc", self._process_btc, args=(progress, task_btc))
            job.add_task("eth", self._process_eth, args=(progress, task_eth))
            job.add_task("sol", self._process_sol, args=(progress, task_sol))
            job.execute()

    def _process_btc(self, progress: Progress, task_id: TaskID) -> None:
        job = ConcurrentTasks(max_workers=self.config.workers.btc)
        for idx, task in enumerate(self.btc):
            job.add_task(str(idx), btc.get_balance, args=(task.address, self.config, progress, task_id))
        job.execute()
        for idx, _task in enumerate(self.btc):
            self.btc[idx].balance = job.result.get(str(idx))  # type: ignore[assignment]

    def _process_eth(self, progress: Progress, task_id: TaskID) -> None:
        job = ConcurrentTasks(max_workers=self.config.workers.eth)
        for idx, task in enumerate(self.eth):
            job.add_task(str(idx), eth.get_balance, args=(task.address, task.token_address, self.config, progress, task_id))
        job.execute()
        for idx, _task in enumerate(self.eth):
            self.eth[idx].balance = job.result.get(str(idx))  # type: ignore[assignment]

    def _process_sol(self, progress: Progress, task_id: TaskID) -> None:
        job = ConcurrentTasks(max_workers=self.config.workers.sol)
        for idx, task in enumerate(self.sol):
            job.add_task(str(idx), solana.get_balance, args=(task.address, self.config, progress, task_id))
        job.execute()
        for idx, _task in enumerate(self.sol):
            self.sol[idx].balance = job.result.get(str(idx))  # type: ignore[assignment]

    @staticmethod
    def from_config(config: Config) -> Balances:
        tasks = Balances(config=config, btc=[], eth=[], sol=[])
        for idx, group in enumerate(config.groups):
            task_list = [Balances.Balance(group_index=idx, address=a, token_address=group.token_address) for a in group.addresses]
            if group.network == Network.BTC:
                tasks.btc.extend(task_list)
            elif group.network == Network.ETH:
                tasks.eth.extend(task_list)
            elif group.network == Network.SOL:
                tasks.sol.extend(task_list)
        return tasks
