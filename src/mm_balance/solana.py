from decimal import Decimal

from mm_solana.balance import sol_balance
from mm_std import Ok, Result

from mm_balance.config import Config
from mm_balance.types import Network


def get_balance(address: str, config: Config) -> Result[Decimal]:
    return sol_balance(address=address, nodes=config.nodes[Network.SOL], proxies=config.proxies, attempts=5, timeout=10).and_then(
        lambda b: Ok(round(Decimal(b / 1_000_000_000), config.round_ndigits)),
    )
