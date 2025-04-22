from decimal import Decimal

from mm_apt import balance
from mm_crypto_utils import Nodes, Proxies, retry
from mm_std import Result

from mm_balance import utils
from mm_balance.constants import RETRIES_BALANCE


async def get_balance(
    nodes: Nodes, wallet: str, token: str | None, decimals: int, proxies: Proxies, round_ndigits: int
) -> Result[Decimal]:
    if token is None:
        token = "0x1::aptos_coin::AptosCoin"  # noqa: S105 # nosec
    return (
        await retry.retry_with_node_and_proxy(
            RETRIES_BALANCE,
            nodes,
            proxies,
            lambda node, proxy: balance.get_balance(node, account=wallet, coin_type=token, proxy=proxy),
        )
    ).map(lambda value: utils.scale_and_round(value, decimals, round_ndigits))
