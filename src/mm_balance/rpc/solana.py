from decimal import Decimal

from mm_solana import balance
from mm_solana import token as solana_token
from mm_std import Ok, Result

from mm_balance.constants import RETRIES_BALANCE, RETRIES_DECIMALS, TIMEOUT_BALANCE, TIMEOUT_DECIMALS


def get_balance(
    nodes: list[str], wallet: str, token: str | None, decimals: int, proxies: list[str], round_ndigits: int
) -> Result[Decimal]:
    if token is None:
        res = balance.get_balance_with_retries(nodes, wallet, retries=RETRIES_BALANCE, timeout=TIMEOUT_BALANCE, proxies=proxies)
    else:
        res = solana_token.get_balance_with_retries(
            nodes, wallet, token, retries=RETRIES_BALANCE, timeout=TIMEOUT_BALANCE, proxies=proxies
        )

    return res.and_then(lambda b: Ok(round(Decimal(b / 10**decimals), round_ndigits)))


def get_token_decimals(nodes: list[str], token_address: str, proxies: list[str]) -> Result[int]:
    return solana_token.get_decimals_with_retries(
        nodes, token_address, retries=RETRIES_DECIMALS, timeout=TIMEOUT_DECIMALS, proxies=proxies
    )
