from collections import defaultdict
from decimal import Decimal

import pydash
from mm_std import hr
from mm_std.random_ import random_str_choice

from mm_balance.config import Config, Group
from mm_balance.constants import RETRIES_COINGECKO_PRICES, TICKER_TO_COINGECKO_ID


class Prices(defaultdict[str, Decimal]):
    """
    A Prices class representing a mapping from coin names to their prices.

    Inherits from:
        Dict[str, Decimal]: A dictionary with coin names as keys and their prices as Decimal values.
    """


def get_prices(config: Config) -> Prices:
    result = Prices()

    coingecko_map: dict[str, str] = {}  # ticker -> coingecko_id

    for group in config.groups:
        coingecko_id = get_coingecko_id(group)
        if coingecko_id:
            coingecko_map[group.ticker] = coingecko_id

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(coingecko_map.values())}&vs_currencies=usd"
    for _ in range(RETRIES_COINGECKO_PRICES):
        res = hr(url, proxy=random_str_choice(config.settings.proxies))
        if res.code != 200:
            continue

        for ticker, coingecko_id in coingecko_map.items():
            if coingecko_id in res.json:
                result[ticker] = Decimal(str(pydash.get(res.json, f"{coingecko_id}.usd")))
        break

    return result


def get_coingecko_id(group: Group) -> str | None:
    if group.coingecko_id:
        return group.coingecko_id
    return TICKER_TO_COINGECKO_ID.get(group.ticker)
