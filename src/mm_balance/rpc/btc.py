from decimal import Decimal

from mm_btc.blockstream import BlockstreamClient
from mm_crypto_utils import Proxies
from mm_std import Result

from mm_balance.constants import RETRIES_BALANCE
from mm_balance.utils import scale_and_round


async def get_balance(address: str, proxies: Proxies, round_ndigits: int) -> Result[Decimal]:
    return (await BlockstreamClient(proxies=proxies, attempts=RETRIES_BALANCE).get_confirmed_balance(address)).map(
        lambda value: scale_and_round(value, 8, round_ndigits)
    )
