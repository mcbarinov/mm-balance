from decimal import Decimal

from mm_crypto_utils import Nodes, Proxies
from mm_eth import retry
from mm_std import Result

from mm_balance.constants import RETRIES_BALANCE, RETRIES_DECIMALS, TIMEOUT_BALANCE, TIMEOUT_DECIMALS
from mm_balance.utils import scale_and_round


async def get_balance(
    nodes: Nodes, wallet: str, token: str | None, decimals: int, proxies: Proxies, round_ndigits: int
) -> Result[Decimal]:
    if token is not None:
        res = await retry.erc20_balance(RETRIES_BALANCE, nodes, proxies, token=token, wallet=wallet, timeout=TIMEOUT_BALANCE)

    else:
        res = await retry.eth_get_balance(RETRIES_BALANCE, nodes, proxies, address=wallet, timeout=TIMEOUT_BALANCE)
    return res.map(lambda value: scale_and_round(value, decimals, round_ndigits))


async def get_token_decimals(nodes: Nodes, token: str, proxies: Proxies) -> Result[int]:
    return await retry.erc20_decimals(RETRIES_DECIMALS, nodes, proxies, token=token, timeout=TIMEOUT_DECIMALS)
