from decimal import Decimal

from mm_btc.blockstream import BlockstreamClient
from mm_std import Ok, Result
from rich.progress import Progress, TaskID

from mm_balance.config import Config


def get_balance(address: str, config: Config, progress: Progress | None = None, task_id: TaskID | None = None) -> Result[Decimal]:
    res: Result[Decimal] = (
        BlockstreamClient(proxies=config.proxies, attempts=3)
        .get_confirmed_balance(address)
        .and_then(
            lambda b: Ok(round(Decimal(b / 100_000_000), config.round_ndigits)),
        )
    )
    if task_id is not None and progress is not None:
        progress.update(task_id, advance=1)
    return res
