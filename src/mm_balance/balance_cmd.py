import getpass
from pathlib import Path

from mm_std import PrintFormat, fatal
from pydantic import BaseModel

from mm_balance.config import Config
from mm_balance.diff import BalancesDict, Diff
from mm_balance.output.formats import json_format, table_format
from mm_balance.price import Prices, get_prices
from mm_balance.result import create_balances_result
from mm_balance.token_decimals import get_token_decimals
from mm_balance.workers import Workers


class BalanceCmdParams(BaseModel):
    config_path: Path
    print_format: PrintFormat | None
    skip_empty: bool | None
    debug: bool | None
    print_config: bool | None
    price: bool | None
    save_balances: Path | None
    diff_from_balances: Path | None


async def run(params: BalanceCmdParams) -> None:
    zip_password = ""  # nosec
    if params.config_path.name.endswith(".zip"):
        zip_password = getpass.getpass("zip password")
    config = Config.read_toml_config_or_exit(params.config_path, zip_password=zip_password)
    if params.print_config:
        config.print_and_exit()

    if params.print_format is not None:
        config.settings.print_format = params.print_format
    if params.debug is not None:
        config.settings.print_debug = params.debug
    if params.skip_empty is not None:
        config.settings.skip_empty = params.skip_empty
    if params.price is not None:
        config.settings.price = params.price

    if config.settings.print_debug and config.settings.print_format is PrintFormat.TABLE:
        table_format.print_nodes(config)
        table_format.print_proxy_count(config)

    token_decimals = await get_token_decimals(config)
    if config.settings.print_debug and config.settings.print_format is PrintFormat.TABLE:
        table_format.print_token_decimals(token_decimals)

    prices = await get_prices(config) if config.settings.price else Prices()
    if config.settings.print_format is PrintFormat.TABLE:
        table_format.print_prices(config, prices)

    workers = Workers(config, token_decimals)
    await workers.process()

    result = create_balances_result(config, prices, workers)
    if config.settings.print_format is PrintFormat.TABLE:
        table_format.print_result(config, result, workers)
    elif config.settings.print_format is PrintFormat.JSON:
        json_format.print_result(config, token_decimals, prices, workers, result)
    else:
        fatal("Unsupported print format")

    if params.save_balances:
        BalancesDict.from_balances_result(result).save_to_path(params.save_balances)

    if params.diff_from_balances:
        old_balances = BalancesDict.from_file(params.diff_from_balances)
        new_balances = BalancesDict.from_balances_result(result)
        diff = Diff.calc(old_balances, new_balances)
        diff.print(config.settings.print_format)
