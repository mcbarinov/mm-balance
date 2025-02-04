from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Annotated, Self

import pydash
from mm_crypto_utils import ConfigValidators
from mm_std import BaseConfig, PrintFormat, fatal
from pydantic import BeforeValidator, Field, StringConstraints, model_validator

from mm_balance.constants import DEFAULT_NODES, TOKEN_ADDRESS, Network


class Validators(ConfigValidators):
    pass


class Group(BaseConfig):
    comment: str = ""
    ticker: Annotated[str, StringConstraints(to_upper=True)]
    network: Network
    token_address: str | None = None  # If None, it's a native token, for example ETH
    token_decimals: int | None = None
    coingecko_id: str | None = None
    addresses: Annotated[list[str], BeforeValidator(Validators.addresses(unique=True))]
    share: Decimal = Decimal(1)

    @property
    def name(self) -> str:
        result = self.ticker
        if self.comment:
            result += " / " + self.comment
        result += " / " + self.network
        return result

    @model_validator(mode="after")
    def final_validator(self) -> Self:
        if self.token_address is None:
            self.token_address = detect_token_address(self.ticker, self.network)
        if self.token_address is not None and self.network.is_evm_network():
            self.token_address = self.token_address.lower()
        return self

    def process_addresses(self, address_groups: list[AddressGroup]) -> None:
        addresses: list[str] = []
        for address in self.addresses:
            if address_group := pydash.find(address_groups, lambda g: g.name == address):  # noqa: B023
                addresses.extend(address_group.addresses)
            else:
                # TODO: check address is valid
                addresses.append(address)
        self.addresses = pydash.uniq(process_file_addresses(addresses))


class AddressGroup(BaseConfig):
    name: str
    addresses: Annotated[list[str], BeforeValidator(ConfigValidators.addresses(unique=True))]


class Settings(BaseConfig):
    proxies: Annotated[list[str], Field(default_factory=list), BeforeValidator(Validators.proxies())]
    round_ndigits: int = 4
    print_format: PrintFormat = PrintFormat.TABLE
    price: bool = True
    skip_empty: bool = False  # don't print the address with an empty balance
    print_debug: bool = False  # print debug info: nodes, token_decimals
    format_number_separator: str = ","  # as thousands separators


class Config(BaseConfig):
    groups: list[Group] = Field(alias="coins")
    addresses: list[AddressGroup] = Field(default_factory=list)
    nodes: dict[Network, list[str]] = Field(default_factory=dict)
    workers: dict[Network, int] = Field(default_factory=dict)
    settings: Settings = Field(default_factory=Settings)  # type: ignore[arg-type]

    def has_share(self) -> bool:
        return any(g.share != Decimal(1) for g in self.groups)

    def networks(self) -> list[Network]:
        return pydash.uniq([group.network for group in self.groups])

    @model_validator(mode="after")
    def final_validator(self) -> Self:
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


def get_address_group_by_name(address_groups: list[AddressGroup], name: str) -> AddressGroup | None:
    return pydash.find(address_groups, lambda g: g.name == name)


def process_file_addresses(addresses: list[str]) -> list[str]:
    result = []
    for address in addresses:
        if address.startswith("file://"):
            path = Path(address.removeprefix("file://"))
            if path.is_file():
                result.extend(path.read_text().strip().splitlines())
            else:
                fatal(f"File with addresses not found: {path}")
        else:
            result.append(address)
    return result
