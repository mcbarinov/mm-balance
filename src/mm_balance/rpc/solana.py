from decimal import Decimal

from mm_solana.balance import sol_balance
from mm_std import Ok, Result
from rich.progress import Progress, TaskID

from mm_balance.config import Config
from mm_balance.types import Network


def get_balance(address: str, config: Config, progress: Progress | None = None, task_id: TaskID | None = None) -> Result[Decimal]:
    res: Result[Decimal] = sol_balance(
        address=address, nodes=config.nodes[Network.SOL], proxies=config.proxies, attempts=5, timeout=10
    ).and_then(
        lambda b: Ok(round(Decimal(b / 1_000_000_000), config.round_ndigits)),
    )
    if task_id is not None and progress is not None:
        progress.update(task_id, advance=1)
    return res
