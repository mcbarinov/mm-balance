from decimal import Decimal

import pydash
from mm_std import fatal, hr
from mm_std.random_ import random_str_choice

from mm_balance.config import Config, Group
from mm_balance.constants import RETRIES_COINGECKO_PRICES, Network


class Prices(dict[str, Decimal]):
    """
    A Prices class representing a mapping from coin names to their prices.

    Inherits from:
        Dict[str, Decimal]: A dictionary with coin names as keys and their prices as Decimal values.
    """


def get_prices(config: Config) -> Prices:
    result = Prices()

    coins = pydash.uniq([group.ticker for group in config.groups])
    coingecko_ids = pydash.uniq([get_coingecko_id(group) for group in config.groups])

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={",".join(coingecko_ids)}&vs_currencies=usd"
    for _ in range(RETRIES_COINGECKO_PRICES):
        res = hr(url, proxy=random_str_choice(config.proxies))
        if res.code != 200:
            continue

        for idx, coin in enumerate(coins):
            if coingecko_ids[idx] in res.json:
                result[coin] = Decimal(str(pydash.get(res.json, f"{coingecko_ids[idx]}.usd")))
            else:
                fatal("Can't get price for {coin} from coingecko, coingecko_id={coingecko_ids[idx]}")

    return result


TICKER_TO_COINGECKO_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "USDT": "tether",
    "USDC": "usd-coin",
    "SOL": "solana",
}


def get_coingecko_id(group: Group) -> str:
    if group.coingecko_id:
        return group.coingecko_id
    elif group.network is Network.BITCOIN:
        return "bitcoin"
    elif group.network is Network.ETHEREUM and group.token_address is None:
        return "ethereum"
    elif group.ticker == "ETH":
        return "ethereum"
    elif group.ticker == "USDT":
        return "tether"
    elif group.ticker == "USDC":
        return "usd-coin"
    elif group.ticker == "SOL":
        return "solana"

    raise ValueError(f"can't get coingecko_id for {group.ticker}")
