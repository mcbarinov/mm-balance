import getpass
import pathlib
import pkgutil
from typing import Annotated

import typer

from mm_balance import output
from mm_balance.balances import Balances
from mm_balance.config import Config
from mm_balance.constants import Network
from mm_balance.price import Prices, get_prices
from mm_balance.token_decimals import get_token_decimals

app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False, add_completion=False)


def example_callback(value: bool) -> None:
    if value:
        data = pkgutil.get_data(__name__, "config/example.yml")
        typer.echo(data)
        raise typer.Exit


def networks_callback(value: bool) -> None:
    if value:
        for network in Network:
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

    prices = get_prices(config) if config.price else Prices()
    output.print_prices(config, prices)

    token_decimals = get_token_decimals(config)
    balances = Balances(config, token_decimals)
    balances.process()

    output.print_groups(balances, config, prices)
    output.print_total(config, balances, prices)


if __name__ == "__main__":
    app()
