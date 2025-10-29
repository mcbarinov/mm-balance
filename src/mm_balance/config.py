from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Annotated, Self

import mm_print
import pydash
from mm_web3 import ConfigValidators, Web3CliConfig
from pydantic import BeforeValidator, Field, StringConstraints, model_validator

from mm_balance.constants import DEFAULT_NODES, TOKEN_ADDRESS, Network
from mm_balance.utils import PrintFormat, evaluate_share_expression


class Validators(ConfigValidators):
    pass


class AssetGroup(Web3CliConfig):
    """
    Represents a group of cryptocurrency assets of the same type.

    An asset group contains information about a specific cryptocurrency (token)
    across multiple addresses/wallets.
    """

    comment: str = ""
    ticker: Annotated[str, StringConstraints(to_upper=True)]
    network: Network
    token: str | None = None  # Token address. If None, it's a native token
    decimals: int | None = None
    coingecko_id: str | None = None
    addresses: Annotated[list[str], BeforeValidator(Validators.addresses(deduplicate=True))]
    share: str = "total"

    @property
    def name(self) -> str:
        result = self.ticker
        if self.comment:
            result += " / " + self.comment
        result += " / " + self.network
        return result

    def evaluate_share(self, balance_sum: Decimal) -> Decimal:
        """Evaluate share expression with actual balance_sum value."""
        return evaluate_share_expression(self.share, balance_sum)

    @model_validator(mode="after")
    def final_validator(self) -> Self:
        if self.token is None:
            self.token = detect_token_address(self.ticker, self.network)
        if self.token is not None and self.network.is_evm_network():
            self.token = self.token.lower()
        return self

    def process_addresses(self, address_groups: list[AddressCollection]) -> None:
        result = []
        for line in self.addresses:
            if line.startswith("file:"):
                path = Path(line.removeprefix("file:").strip()).expanduser()
                if path.is_file():
                    result += path.read_text().strip().splitlines()
                else:
                    mm_print.exit_with_error(f"File with addresses not found: {path}")
            elif line.startswith("group:"):
                group_name = line.removeprefix("group:").strip()
                address_group = next((ag for ag in address_groups if ag.name == group_name), None)
                if address_group is None:
                    raise ValueError(f"Address group not found: {group_name}")
                result += address_group.addresses
            else:
                result.append(line)
        # TODO: check address is valid. There is network info in the group
        if self.network.need_lowercase_address():
            result = [address.lower() for address in result]
        self.addresses = pydash.uniq(result)


class AddressCollection(Web3CliConfig):
    name: str
    addresses: Annotated[list[str], BeforeValidator(Validators.addresses(deduplicate=True))]


class Settings(Web3CliConfig):
    proxies: Annotated[list[str], Field(default_factory=list), BeforeValidator(Validators.proxies())]
    round_ndigits: int = 4
    print_format: PrintFormat = PrintFormat.TABLE
    price: bool = True
    skip_empty: bool = False  # don't print the address with an empty balance
    print_debug: bool = False  # print debug info: nodes, token_decimals
    format_number_separator: str = ","  # as thousands separators


class Config(Web3CliConfig):
    groups: list[AssetGroup] = Field(alias="coins")
    addresses: list[AddressCollection] = Field(default_factory=list)
    nodes: dict[Network, list[str]] = Field(default_factory=dict)
    workers: dict[Network, int] = Field(default_factory=dict)
    settings: Settings = Field(default_factory=Settings)  # type: ignore[arg-type]

    def has_share(self) -> bool:
        return any(g.share != "total" for g in self.groups)

    def networks(self) -> list[Network]:
        return pydash.uniq([group.network for group in self.groups])

    @model_validator(mode="after")
    def final_validator(self) -> Self:
        # check all addresses has uniq name
        address_group_names = [ag.name for ag in self.addresses]
        non_uniq_names = [name for name in address_group_names if address_group_names.count(name) > 1]
        if non_uniq_names:
            raise ValueError("There are non-unique address group names: " + ", ".join(non_uniq_names))

        # load addresses from address_group
        for group in self.groups:
            group.process_addresses(self.addresses)

        # load default rpc nodes
        for network in self.networks():
            if network not in self.nodes:
                self.nodes[network] = DEFAULT_NODES[network]

        # load default workers
        for network in self.networks():
            if network not in self.workers:
                self.workers[network] = 5

        return self


def detect_token_address(ticker: str, network: Network) -> str | None:
    if network in TOKEN_ADDRESS:
        return TOKEN_ADDRESS[network].get(ticker)
