from decimal import Decimal

from mm_aptos import balance
from mm_std import Result

from mm_balance.constants import RETRIES_BALANCE, TIMEOUT_BALANCE


def get_balance(
    nodes: list[str], wallet: str, token: str | None, decimals: int, proxies: list[str], round_ndigits: int
) -> Result[Decimal]:
    if token is None:
        token = "0x1::aptos_coin::AptosCoin"  # nosec
    return balance.get_decimal_balance_with_retries(
        RETRIES_BALANCE,
        nodes,
        wallet,
        token,
        decimals=decimals,
        timeout=TIMEOUT_BALANCE,
        proxies=proxies,
        round_ndigits=round_ndigits,
    )
