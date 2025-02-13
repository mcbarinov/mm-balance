import getpass
import importlib.metadata
import pkgutil
from pathlib import Path
from typing import Annotated

import typer
from mm_std import PrintFormat, fatal, pretty_print_toml

from mm_balance.config import Config
from mm_balance.constants import NETWORKS
from mm_balance.diff import BalancesDict, Diff
from mm_balance.output.formats import json_format, table_format
from mm_balance.price import Prices, get_prices
from mm_balance.result import create_balances_result
from mm_balance.token_decimals import get_token_decimals
from mm_balance.workers import Workers

app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False, add_completion=False)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"mm-balance: v{importlib.metadata.version('mm-balance')}")
        raise typer.Exit


def example_callback(value: bool) -> None:
    if value:
        data = pkgutil.get_data(__name__, "config/example.toml")
        if data is None:
            fatal("Example config not found")
        pretty_print_toml(data.decode("utf-8"))
        raise typer.Exit


def networks_callback(value: bool) -> None:
    if value:
        for network in NETWORKS:
            typer.echo(network)
        raise typer.Exit


@app.command()
def cli(
    config_path: Annotated[Path, typer.Argument()],
    print_format: Annotated[PrintFormat | None, typer.Option("--format", "-f", help="Print format.")] = None,
    skip_empty: Annotated[bool | None, typer.Option("--skip-empty", "-s", help="Skip empty balances.")] = None,
    debug: Annotated[bool | None, typer.Option("--debug", "-d", help="Print debug info.")] = None,
    print_config: Annotated[bool | None, typer.Option("--config", "-c", help="Print config and exit.")] = None,
    price: Annotated[bool | None, typer.Option("--price/--no-price", help="Print prices.")] = None,
    save_balances_file: Annotated[Path | None, typer.Option("--save-balances-file", help="Save balances file.")] = None,
    diff_from_balances_file: Annotated[
        Path | None, typer.Option("--diff-from-balances-file", help="Diff from balances file.")
    ] = None,
    _example: Annotated[bool | None, typer.Option("--example", callback=example_callback, help="Print a config example.")] = None,
    _networks: Annotated[
        bool | None, typer.Option("--networks", callback=networks_callback, help="Print supported networks.")
    ] = None,
    _version: bool = typer.Option(None, "--version", callback=version_callback, is_eager=True),
) -> None:
    zip_password = ""  # nosec
    if config_path.name.endswith(".zip"):
        zip_password = getpass.getpass("zip password")
    config = Config.read_toml_config_or_exit(config_path, zip_password=zip_password)
    if print_config:
        config.print_and_exit()

    if print_format is not None:
        config.settings.print_format = print_format
    if debug is not None:
        config.settings.print_debug = debug
    if skip_empty is not None:
        config.settings.skip_empty = skip_empty
    if price is not None:
        config.settings.price = price

    if config.settings.print_debug and config.settings.print_format is PrintFormat.TABLE:
        table_format.print_nodes(config)
        table_format.print_proxy_count(config)

    token_decimals = get_token_decimals(config)
    if config.settings.print_debug and config.settings.print_format is PrintFormat.TABLE:
        table_format.print_token_decimals(token_decimals)

    prices = get_prices(config) if config.settings.price else Prices()
    if config.settings.print_format is PrintFormat.TABLE:
        table_format.print_prices(config, prices)

    workers = Workers(config, token_decimals)
    workers.process()

    result = create_balances_result(config, prices, workers)
    if config.settings.print_format is PrintFormat.TABLE:
        table_format.print_result(config, result, workers)
    elif config.settings.print_format is PrintFormat.JSON:
        json_format.print_result(config, token_decimals, prices, workers, result)
    else:
        fatal("Unsupported print format")

    if save_balances_file:
        BalancesDict.from_balances_result(result).save_to_path(save_balances_file)

    if diff_from_balances_file:
        old_balances = BalancesDict.from_file(diff_from_balances_file)
        new_balances = BalancesDict.from_balances_result(result)
        diff = Diff.calc(old_balances, new_balances)
        diff.print(config.settings.print_format)


if __name__ == "__main__":
    app()
