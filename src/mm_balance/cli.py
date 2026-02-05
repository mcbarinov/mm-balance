import asyncio
import importlib.metadata
import pkgutil
from pathlib import Path
from typing import Annotated

import typer
from mm_print import print_toml

from mm_balance import command_runner
from mm_balance.command_runner import CommandParameters
from mm_balance.constants import NETWORKS
from mm_balance.utils import PrintFormat, fatal

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
        print_toml(data.decode("utf-8"))
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
    save_balances: Annotated[Path | None, typer.Option("--save-balances", help="Save balances file.")] = None,
    diff_from_balances: Annotated[Path | None, typer.Option("--diff-from-balances", help="Diff from balances file.")] = None,
    _example: Annotated[bool | None, typer.Option("--example", callback=example_callback, help="Print a config example.")] = None,
    _networks: Annotated[
        bool | None, typer.Option("--networks", callback=networks_callback, help="Print supported networks.")
    ] = None,
    _version: bool = typer.Option(None, "--version", callback=version_callback, is_eager=True),
) -> None:
    asyncio.run(
        command_runner.run(
            CommandParameters(
                config_path=config_path,
                print_format=print_format,
                skip_empty=skip_empty,
                debug=debug,
                print_config=print_config,
                price=price,
                save_balances=save_balances,
                diff_from_balances=diff_from_balances,
            )
        )
    )


if __name__ == "__main__":
    app()
