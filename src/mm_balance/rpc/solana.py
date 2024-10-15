from decimal import Decimal

from mm_solana import balance, token
from mm_std import Ok, Result

from mm_balance.constants import RETRIES_BALANCE, RETRIES_DECIMALS, TIMEOUT_BALANCE, TIMEOUT_DECIMALS


def get_native_balance(nodes: list[str], address: str, proxies: list[str], round_ndigits: int) -> Result[Decimal]:
    return balance.get_balance_with_retries(
        nodes, address, retries=RETRIES_BALANCE, timeout=TIMEOUT_BALANCE, proxies=proxies
    ).and_then(lambda b: Ok(round(Decimal(b / 1_000_000_000), round_ndigits)))


def get_token_balance(
    nodes: list[str], wallet_address: str, token_address: str, decimals: int, proxies: list[str], round_ndigits: int
) -> Result[Decimal]:
    return token.get_balance_with_retries(
        nodes, wallet_address, token_address, retries=RETRIES_BALANCE, timeout=TIMEOUT_BALANCE, proxies=proxies
    ).and_then(lambda b: Ok(round(Decimal(b / 10**decimals), round_ndigits)))


def get_token_decimals(nodes: list[str], token_address: str, proxies: list[str]) -> Result[int]:
    return token.get_decimals_with_retries(
        nodes, token_address, retries=RETRIES_DECIMALS, timeout=TIMEOUT_DECIMALS, proxies=proxies
    )
