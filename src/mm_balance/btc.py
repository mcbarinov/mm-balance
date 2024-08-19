from decimal import Decimal

from mm_btc.blockstream import BlockstreamClient
from mm_std import Ok, Result

from mm_balance.config import Config


def get_balance(address: str, config: Config) -> Result[Decimal]:
    return (
        BlockstreamClient(proxies=config.proxies, attempts=3)
        .get_confirmed_balance(address)
        .and_then(
            lambda b: Ok(round(Decimal(b / 100_000_000), config.round_ndigits)),
        )
    )
