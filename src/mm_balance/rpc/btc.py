from decimal import Decimal

from mm_btc.blockstream import BlockstreamClient
from mm_std import Ok, Result

from mm_balance.constants import RETRIES_BALANCE


def get_balance(address: str, proxies: list[str], round_ndigits: int) -> Result[Decimal]:
    return (
        BlockstreamClient(proxies=proxies, attempts=RETRIES_BALANCE)
        .get_confirmed_balance(address)
        .and_then(
            lambda b: Ok(round(Decimal(b / 100_000_000), round_ndigits)),
        )
    )
