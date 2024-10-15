from decimal import Decimal

import pydash
from mm_std import fatal, hr
from mm_std.random_ import random_str_choice

from mm_balance.config import Config, Group
from mm_balance.constants import RETRIES_COINGECKO_PRICES, EthTokenAddress, Network


class Prices(dict[str, Decimal]):
    """
    A Prices class representing a mapping from coin names to their prices.

    Inherits from:
        Dict[str, Decimal]: A dictionary with coin names as keys and their prices as Decimal values.
    """


def get_prices(config: Config) -> Prices:
    result = Prices()

    coins = pydash.uniq([group.coin for group in config.groups])
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


def get_coingecko_id(group: Group) -> str:
    if group.coingecko_id:
        return group.coingecko_id
    elif group.network is Network.BTC:
        return "bitcoin"
    elif group.network is Network.ETH and group.token_address is None:
        return "ethereum"
    elif group.coin.lower() == "usdt" or (group.token_address is not None and group.token_address == EthTokenAddress.USDT):
        return "tether"
    elif group.coin.lower() == "usdc" or (group.token_address is not None and group.token_address == EthTokenAddress.USDC):
        return "usd-coin"
    elif group.coin.lower() == "sol":
        return "solana"

    raise ValueError(f"can't get coingecko_id for {group.coin}")
