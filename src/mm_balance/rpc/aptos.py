from decimal import Decimal

from mm_aptos import balance
from mm_std import Result

from mm_balance.constants import RETRIES_BALANCE, TIMEOUT_BALANCE


def get_native_balance(nodes: list[str], address: str, proxies: list[str], round_ndigits: int) -> Result[Decimal]:
    return balance.get_decimal_balance_with_retries(
        RETRIES_BALANCE,
        nodes,
        address,
        "0x1::aptos_coin::AptosCoin",
        decimals=8,
        timeout=TIMEOUT_BALANCE,
        proxies=proxies,
        round_ndigits=round_ndigits,
    )


def get_token_balance(
    nodes: list[str], address: str, token_address: str, decimals: int, proxies: list[str], round_ndigits: int
) -> Result[Decimal]:
    return balance.get_decimal_balance_with_retries(
        RETRIES_BALANCE,
        nodes,
        address,
        token_address,
        decimals=decimals,
        timeout=TIMEOUT_BALANCE,
        proxies=proxies,
        round_ndigits=round_ndigits,
    )
