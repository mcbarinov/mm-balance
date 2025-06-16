from collections import defaultdict
from decimal import Decimal

import pydash
from mm_http import http_request
from mm_web3 import random_proxy

from mm_balance.config import AssetGroup, Config
from mm_balance.constants import RETRIES_COINGECKO_PRICES, TICKER_TO_COINGECKO_ID


class Prices(defaultdict[str, Decimal]):
    """
    A Prices class representing a mapping from coin names to their prices.

    Inherits from:
        Dict[str, Decimal]: A dictionary with coin names as keys and their prices as Decimal values.
    """


async def get_prices(config: Config) -> Prices:
    result = Prices()

    coingecko_map: dict[str, str] = {}  # ticker -> coingecko_id

    for group in config.groups:
        coingecko_id = get_coingecko_id(group)
        if coingecko_id:
            coingecko_map[group.ticker] = coingecko_id

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(coingecko_map.values())}&vs_currencies=usd"
    for _ in range(RETRIES_COINGECKO_PRICES):
        res = await http_request(url, proxy=random_proxy(config.settings.proxies))
        if res.status_code != 200:
            continue

        json_body = res.parse_json_body() or {}

        for ticker, coingecko_id in coingecko_map.items():
            if coingecko_id in json_body:
                result[ticker] = Decimal(str(pydash.get(json_body, f"{coingecko_id}.usd")))
        break

    return result


def get_coingecko_id(group: AssetGroup) -> str | None:
    if group.coingecko_id:
        return group.coingecko_id
    return TICKER_TO_COINGECKO_ID.get(group.ticker)
