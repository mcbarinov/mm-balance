import getpass
import pathlib

import click

from mm_balance import output
from mm_balance.balances import Balances
from mm_balance.config import Config
from mm_balance.price import get_prices


@click.command()
@click.argument("config_path", type=click.Path(exists=True, path_type=pathlib.Path))
def cli(config_path: pathlib.Path) -> None:
    zip_password = ""  # nosec
    if config_path.name.endswith(".zip"):
        zip_password = getpass.getpass("zip password")
    config = Config.read_config(config_path, zip_password=zip_password)

    prices = get_prices(config) if config.price else {}
    balances = Balances.from_config(config)
    balances.process()

    output.print_groups(balances, config, prices)
    output.print_prices(config, prices)
    output.print_total(config, balances, prices)
