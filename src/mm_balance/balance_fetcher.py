from dataclasses import dataclass
from decimal import Decimal

from mm_concurrency import AsyncTaskRunner
from mm_result import Result
from rich.progress import TaskID

from mm_balance import rpc
from mm_balance.config import Config
from mm_balance.constants import Network
from mm_balance.output import utils
from mm_balance.token_decimals import TokenDecimals
from mm_balance.utils import PrintFormat


@dataclass
class Task:
    group_index: int
    wallet_address: str
    token_address: str | None
    balance: Result[Decimal] | None = None


class BalanceFetcher:
    def __init__(self, config: Config, token_decimals: TokenDecimals) -> None:
        self.config = config
        self.token_decimals = token_decimals
        self.tasks: dict[Network, list[Task]] = {network: [] for network in config.networks()}
        self.progress_bar = utils.create_progress_bar(config.settings.print_format is not PrintFormat.TABLE)
        self.progress_bar_task: dict[Network, TaskID] = {}

        for idx, group in enumerate(config.groups):
            task_list = [Task(group_index=idx, wallet_address=a, token_address=group.token) for a in group.addresses]
            self.tasks[group.network].extend(task_list)

        for network in config.networks():
            if self.tasks[network]:
                self.progress_bar_task[network] = utils.create_progress_task(self.progress_bar, network, len(self.tasks[network]))

    async def process(self) -> None:
        with self.progress_bar:
            runner = AsyncTaskRunner(concurrency=10)
            for network in self.config.networks():
                runner.add(f"process_{network}", self._process_network(network))
            await runner.run()

    def get_group_tasks(self, group_index: int, network: Network) -> list[Task]:
        return [b for b in self.tasks[network] if b.group_index == group_index]

    def get_errors(self) -> list[Task]:
        result = []
        for network in self.tasks:
            result.extend([task for task in self.tasks[network] if task.balance is not None and task.balance.is_err()])
        return result

    async def _process_network(self, network: Network) -> None:
        runner = AsyncTaskRunner(concurrency=self.config.workers[network])
        for idx, task in enumerate(self.tasks[network]):
            runner.add(str(idx), self._get_balance(network, task.wallet_address, task.token_address))
        res = await runner.run()

        # TODO: print job.exceptions if present
        for idx, _task in enumerate(self.tasks[network]):
            self.tasks[network][idx].balance = res.results.get(str(idx))

    async def _get_balance(self, network: Network, wallet_address: str, token_address: str | None) -> Result[Decimal]:
        res = await rpc.get_balance(
            network=network,
            nodes=self.config.nodes[network],
            proxies=self.config.settings.proxies,
            wallet_address=wallet_address,
            token_address=token_address,
            token_decimals=self.token_decimals[network][token_address],
            ndigits=self.config.settings.round_ndigits,
        )
        self.progress_bar.update(self.progress_bar_task[network], advance=1)
        return res
