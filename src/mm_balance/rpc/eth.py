from decimal import Decimal

from mm_eth import erc20, rpc
from mm_std import Ok, Result
from rich.progress import Progress, TaskID

from mm_balance.config import Config
from mm_balance.types import Network


def get_balance(
    address: str, token_address: str | None, config: Config, progress: Progress | None = None, task_id: TaskID | None = None
) -> Result[Decimal]:
    res: Result[Decimal]

    if token_address is not None:
        res = erc20.get_balance(
            config.nodes[Network.ETH],
            token_address,
            address,
            proxies=config.proxies,
            attempts=5,
            timeout=10,
        ).and_then(
            lambda b: Ok(round(Decimal(b / 10 ** config.token_decimals.eth[token_address]), config.round_ndigits)),
        )
    else:
        res = rpc.eth_get_balance(config.nodes[Network.ETH], address, proxies=config.proxies, attempts=5, timeout=10).and_then(
            lambda b: Ok(round(Decimal(b / 10**18), config.round_ndigits)),
        )

    if task_id is not None and progress is not None:
        progress.update(task_id, advance=1)
    return res


def get_token_decimals(token_address: str, config: Config) -> Result[int]:
    return erc20.get_decimals(config.nodes[Network.ETH], token_address, timeout=10, proxies=config.proxies, attempts=5)
