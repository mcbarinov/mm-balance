from decimal import Decimal

import pydash
from mm_std import Err, Ok, Result, fatal, hr
from mm_std.random_ import random_str_choice

from mm_balance.config import Config
from mm_balance.types import EthTokenAddress, Network


def get_prices(config: Config) -> dict[str, Decimal]:
    result = {}
    for group in config.groups:
        res = get_asset_price(coingecko_id(group), config.proxies)
        if isinstance(res, Ok):
            result[group.coin] = res.ok
        else:
            fatal(res.err)
            # raise ValueError(res.err)
    return result


def get_asset_price(coingecko_asset_id: str, proxies: list[str]) -> Result[Decimal]:
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coingecko_asset_id}&vs_currencies=usd"
    data = None
    for _ in range(3):
        res = hr(url, proxy=random_str_choice(proxies))
        data = res.to_dict()
        if res.json and coingecko_asset_id in coingecko_asset_id in res.json:
            return Ok(Decimal(pydash.get(res.json, f"{coingecko_asset_id}.usd")))
    return Err("error", data=data)


def coingecko_id(group: Config.Group) -> str:
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

    raise ValueError(f"can't get coingecko_id for {group.coin}")
