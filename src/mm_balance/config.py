from __future__ import annotations

from decimal import Decimal
from typing import Any, Self

import pydash
from mm_std import BaseConfig, Err, PrintFormat, fatal, hr
from pydantic import Field, field_validator, model_validator

from mm_balance.types import DEFAULT_ETH_NODES, EthTokenAddress, Network


class Config(BaseConfig):
    class Group(BaseConfig):
        comment: str = ""
        coin: str
        network: Network
        token_address: str | None = None
        coingecko_id: str | None = None
        addresses: list[str] = Field(default_factory=list)
        share: Decimal = Decimal(1)

        @property
        def name(self) -> str:
            result = self.coin
            if self.comment:
                result += " / " + self.comment
            return result

        @field_validator("coin", mode="after")
        def coin_validator(cls, v: str) -> str:
            return v.upper()

        @field_validator("addresses", mode="before")
        def to_list_validator(cls, v: str | list[str] | None) -> list[str]:
            return cls.to_list_str_validator(v, unique=True, remove_comments=True, split_line=True)

        @model_validator(mode="before")
        def before_all(cls, data: Any) -> Any:
            if "network" not in data:
                data["network"] = detect_network(data["coin"])
            return data

        @model_validator(mode="after")
        def final_validator(self) -> Self:
            if self.token_address is None:
                self.token_address = detect_token_address(self.coin, self.network)
            if self.token_address is not None and self.network is Network.ETH:
                self.token_address = self.token_address.lower()
            return self

        def process_addresses(self, address_groups: list[Config.AddressGroup]) -> None:
            addresses: list[str] = []
            for address in self.addresses:
                if address_group := pydash.find(address_groups, lambda g: g.name == address):  # noqa: B023
                    addresses.extend(address_group.addresses)
                else:
                    # TODO: check address is valid
                    addresses.append(address)
            self.addresses = addresses

    class AddressGroup(BaseConfig):
        name: str
        addresses: list[str]

        @field_validator("addresses", mode="before")
        def to_list_validator(cls, v: str | list[str] | None) -> list[str]:
            return cls.to_list_str_validator(v, unique=True, remove_comments=True, split_line=True)

    class Workers(BaseConfig):
        btc: int = 5
        eth: int = 5

    class TokenDecimals(BaseConfig):
        eth: dict[str, int] = Field(default_factory=dict)

    groups: list[Group]
    addresses: list[AddressGroup] = Field(default_factory=list)

    proxies_url: str | None = None
    proxies: list[str] = Field(default_factory=list)
    round_ndigits: int = 4
    nodes: dict[Network, list[str]] = Field(default_factory=dict)
    print_format: PrintFormat = PrintFormat.TABLE
    price: bool = True

    # non configs
    workers: Workers = Workers()
    token_decimals: TokenDecimals = TokenDecimals()

    def btc_groups(self) -> list[Group]:
        return [g for g in self.groups if g.network == Network.BTC]

    def eth_groups(self) -> list[Group]:
        return [g for g in self.groups if g.network == Network.ETH]

    def has_sum_share(self) -> bool:
        return any(g.share != Decimal(1) for g in self.groups)

    @model_validator(mode="after")
    def final_validator(self) -> Self:
        # load from proxies_url
        if self.proxies_url is not None:
            self.proxies = get_proxies(self.proxies_url)

        # load addresses from address_group
        for group in self.groups:
            group.process_addresses(self.addresses)

        # load default rpc nodes
        if Network.BTC not in self.nodes:
            self.nodes[Network.BTC] = []
        if Network.ETH not in self.nodes:
            self.nodes[Network.ETH] = DEFAULT_ETH_NODES

        # load token decimals
        for group in self.groups:
            if group.network == Network.ETH and group.token_address is not None:
                from mm_balance import eth

                decimals_res = eth.get_token_decimals(group.token_address, self)
                if isinstance(decimals_res, Err):
                    fatal(f"can't get decimals for token {group.coin} / {group.token_address}, error={decimals_res.err}")
                self.token_decimals.eth[group.token_address] = decimals_res.ok

        return self


def detect_network(coin: str) -> Network:
    coin = coin.lower()
    if coin == "btc":
        return Network.BTC
    if coin == "eth":
        return Network.ETH
    return Network.ETH
    # raise ValueError(f"can't get network for the coin: {coin}")


def detect_token_address(coin: str, network: str) -> str | None:
    if network == Network.ETH.lower():
        if coin.lower() == "usdt":
            return EthTokenAddress.USDT
        if coin.lower() == "usdc":
            return EthTokenAddress.USDC


def get_proxies(proxies_url: str) -> list[str]:
    try:
        res = hr(proxies_url)
        if res.is_error():
            fatal(f"Can't get proxies: {res.error}")
        proxies = [p.strip() for p in res.body.splitlines() if p.strip()]
        return pydash.uniq(proxies)
    except Exception as err:
        fatal(f"Can't get  proxies: {err}")


def get_address_group_by_name(address_groups: list[Config.AddressGroup], name: str) -> Config.AddressGroup | None:
    return pydash.find(address_groups, lambda g: g.name == name)
