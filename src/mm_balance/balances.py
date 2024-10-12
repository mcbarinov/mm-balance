from __future__ import annotations

from decimal import Decimal

from mm_std import ConcurrentTasks, Result
from pydantic import BaseModel

from mm_balance import btc, eth
from mm_balance.config import Config
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

    def network_tasks(self, network: Network) -> list[Balance]:
        if network == Network.BTC:
            return self.btc
        elif network == Network.ETH:
            return self.eth
        else:
            raise ValueError

    def get_group_balances(self, group_index: int, network: Network) -> list[Balance]:
        # TODO: can we get network by group_index?
        if network == Network.BTC:
            network_balances = self.btc
        elif network == Network.ETH:
            network_balances = self.eth
        else:
            raise ValueError

        return [b for b in network_balances if b.group_index == group_index]

    def process(self) -> None:
        job = ConcurrentTasks()
        job.add_task("btc", self._process_btc)
        job.add_task("eth", self._process_eth)
        job.execute()

    def _process_btc(self) -> None:
        job = ConcurrentTasks(max_workers=self.config.workers.btc)
        for idx, task in enumerate(self.btc):
            job.add_task(str(idx), btc.get_balance, args=(task.address, self.config))
        job.execute()
        for idx, _task in enumerate(self.btc):
            self.btc[idx].balance = job.result.get(str(idx))  # type: ignore[assignment]

    def _process_eth(self) -> None:
        job = ConcurrentTasks(max_workers=self.config.workers.eth)
        for idx, task in enumerate(self.eth):
            job.add_task(str(idx), eth.get_balance, args=(task.address, task.token_address, self.config))
        job.execute()
        for idx, _task in enumerate(self.eth):
            self.eth[idx].balance = job.result.get(str(idx))  # type: ignore[assignment]

    @staticmethod
    def from_config(config: Config) -> Balances:
        tasks = Balances(config=config, btc=[], eth=[])
        for idx, group in enumerate(config.groups):
            task_list = [Balances.Balance(group_index=idx, address=a, token_address=group.token_address) for a in group.addresses]
            if group.network == Network.BTC:
                tasks.btc.extend(task_list)
            elif group.network == Network.ETH:
                tasks.eth.extend(task_list)
        return tasks
