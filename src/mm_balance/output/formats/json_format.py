from mm_std import print_json

from mm_balance.config import Config
from mm_balance.price import Prices
from mm_balance.result import BalancesResult
from mm_balance.token_decimals import TokenDecimals
from mm_balance.workers import Workers


def print_result(config: Config, token_decimals: TokenDecimals, prices: Prices, workers: Workers, result: BalancesResult) -> None:
    data: dict[str, object] = {}
    if config.print_debug:
        data["nodes"] = config.nodes
        data["token_decimals"] = token_decimals
    if config.price:
        data["prices"] = prices

    data["groups"] = result.groups
    data["total"] = result.total
    if config.has_share():
        data["total_share"] = result.total_share

    errors = workers.get_errors()
    if errors:
        data["errors"] = errors

    print_json(data)
