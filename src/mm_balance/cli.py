import getpass
import pathlib
import pkgutil
from typing import Annotated

import typer
from mm_std import PrintFormat, fatal

from mm_balance.config import Config
from mm_balance.constants import NETWORKS
from mm_balance.output.formats import json_format, table_format
from mm_balance.price import Prices, get_prices
from mm_balance.result import create_balances_result
from mm_balance.token_decimals import get_token_decimals
from mm_balance.workers import Workers

app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False, add_completion=False)


def example_callback(value: bool) -> None:
    if value:
        data = pkgutil.get_data(__name__, "config/example.yml")
        typer.echo(data)
        raise typer.Exit


def networks_callback(value: bool) -> None:
    if value:
        for network in NETWORKS:
            typer.echo(network)
        raise typer.Exit


@app.command()
def cli(
    config_path: Annotated[pathlib.Path, typer.Argument()],
    _example: Annotated[bool | None, typer.Option("--example", callback=example_callback, help="Print a config example.")] = None,
    _networks: Annotated[
        bool | None, typer.Option("--networks", callback=networks_callback, help="Print supported networks.")
    ] = None,
) -> None:
    zip_password = ""  # nosec
    if config_path.name.endswith(".zip"):
        zip_password = getpass.getpass("zip password")
    config = Config.read_config(config_path, zip_password=zip_password)

    if config.print_debug and config.print_format is PrintFormat.TABLE:
        table_format.print_nodes(config)

    token_decimals = get_token_decimals(config)
    if config.print_debug and config.print_format is PrintFormat.TABLE:
        table_format.print_token_decimals(token_decimals)

    prices = get_prices(config) if config.price else Prices()
    if config.print_format is PrintFormat.TABLE:
        table_format.print_prices(config, prices)

    workers = Workers(config, token_decimals)
    workers.process()

    result = create_balances_result(config, prices, workers)
    if config.print_format is PrintFormat.TABLE:
        table_format.print_result(config, result, workers)
    elif config.print_format is PrintFormat.JSON:
        json_format.print_result(config, token_decimals, prices, workers, result)
    else:
        fatal("Unsupported print format")

    # print_result(config, result)

    # balances = Balances(config, token_decimals)
    # balances.process()
    #
    # output.print_groups(balances, config, prices)
    # output.print_total(config, balances, prices)
    # output.print_errors(config, balances)


if __name__ == "__main__":
    app()
