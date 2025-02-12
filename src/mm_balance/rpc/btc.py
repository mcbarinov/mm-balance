from decimal import Decimal

from mm_btc.blockstream import BlockstreamClient
from mm_std import Ok, Result

from mm_balance.constants import RETRIES_BALANCE
from mm_balance.utils import scale_and_round


def get_balance(address: str, proxies: list[str], round_ndigits: int) -> Result[Decimal]:
    return (
        BlockstreamClient(proxies=proxies, attempts=RETRIES_BALANCE)
        .get_confirmed_balance(address)
        .and_then(lambda b: Ok(scale_and_round(b, 8, round_ndigits)))
    )
