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
        address_group: str | None = None
        sum_ratio: Decimal = Decimal(1)

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

    class Addresses(BaseConfig):
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
    addresses: list[Addresses] = Field(default_factory=list)

    mm_proxies_app: str | None = None
    proxies: list[str] = Field(default_factory=list)
    round_ndigits: int = 4
    nodes: dict[Network, list[str]] = Field(default_factory=dict)
    print_format: PrintFormat = PrintFormat.TABLE
    price: bool = False

    # non configs
    workers: Workers = Workers()
    token_decimals: TokenDecimals = TokenDecimals()

    def btc_groups(self) -> list[Group]:
        return [g for g in self.groups if g.network == Network.BTC]

    def eth_groups(self) -> list[Group]:
        return [g for g in self.groups if g.network == Network.ETH]

    def has_sum_ratio(self) -> bool:
        return any(g.sum_ratio != Decimal(1) for g in self.groups)

    @model_validator(mode="after")
    def final_validator(self) -> Self:
        # load mm_proxies
        if self.mm_proxies_app is not None:
            self.proxies = get_proxies(self.mm_proxies_app)

        # load addresses
        for group in self.groups:
            if group.address_group is not None:
                address_group = pydash.find(self.addresses, lambda g: g.name == group.address_group)  # noqa: B023
                if address_group is None:
                    fatal(f"can't find address group: {group.address_group}")
                group.addresses.extend(address_group.addresses)
            group.addresses = pydash.uniq(group.addresses)

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
        if coin.lower() == "sdai":
            return EthTokenAddress.SDAI


def get_proxies(mm_proxies_app: str) -> list[str]:
    try:
        url, token = mm_proxies_app.split("|")
        res = hr(url + "/api/proxies/live", headers={"access-token": token})
        return res.json["proxies"]  # type: ignore[no-any-return]
    except Exception as err:
        fatal(f"Can't get  proxies: {err}")
