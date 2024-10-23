from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Self

import pydash
from mm_std import BaseConfig, PrintFormat, fatal, hr
from pydantic import Field, field_validator, model_validator

from mm_balance.constants import DEFAULT_NODES, TOKEN_ADDRESS, Network


class Group(BaseConfig):
    comment: str = ""
    ticker: str
    network: Network
    token_address: str | None = None  # If None, it's a native token, for example ETH
    token_decimals: int | None = None
    coingecko_id: str | None = None
    addresses: list[str] = Field(default_factory=list)
    share: Decimal = Decimal(1)

    @property
    def name(self) -> str:
        result = self.ticker
        if self.comment:
            result += " / " + self.comment
        result += " / " + self.network
        return result

    @field_validator("ticker", mode="after")
    def ticker_validator(cls, v: str) -> str:
        return v.upper()

    @field_validator("addresses", mode="before")
    def to_list_validator(cls, v: str | list[str] | None) -> list[str]:
        return cls.to_list_str_validator(v, unique=True, remove_comments=True, split_line=True)

    # @model_validator(mode="before")
    # def before_all(cls, data: Any) -> Any:
    #     if "network" not in data:
    #         data["network"] = detect_network(data["coin"])
    #     return data

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
    addresses: list[str]

    @field_validator("addresses", mode="before")
    def to_list_validator(cls, v: str | list[str] | None) -> list[str]:
        return cls.to_list_str_validator(v, unique=True, remove_comments=True, split_line=True)


class Config(BaseConfig):
    groups: list[Group] = Field(alias="coins")
    addresses: list[AddressGroup] = Field(default_factory=list)

    proxies_url: str | None = None
    proxies: list[str] = Field(default_factory=list)
    round_ndigits: int = 4
    nodes: dict[Network, list[str]] = Field(default_factory=dict)
    print_format: PrintFormat = PrintFormat.TABLE
    price: bool = True
    skip_empty: bool = False  # don't print the address with an empty balance
    print_debug: bool = False  # print debug info: nodes, token_decimals
    format_number_separator: str = ","  #  as thousands separators
    workers: dict[Network, int] = Field(default_factory=dict)

    def has_share(self) -> bool:
        return any(g.share != Decimal(1) for g in self.groups)

    def networks(self) -> list[Network]:
        return pydash.uniq([group.network for group in self.groups])

    @model_validator(mode="after")
    def final_validator(self) -> Self:
        # load from proxies_url
        if self.proxies_url is not None:
            self.proxies = get_proxies(self.proxies_url)

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


def get_proxies(proxies_url: str) -> list[str]:
    try:
        res = hr(proxies_url)
        if res.is_error():
            fatal(f"Can't get proxies: {res.error}")
        proxies = [p.strip() for p in res.body.splitlines() if p.strip()]
        return pydash.uniq(proxies)
    except Exception as err:
        fatal(f"Can't get  proxies: {err}")


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
