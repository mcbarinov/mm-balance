from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Self

from mm_std import Ok, PrintFormat, print_table

from mm_balance.balances import Balances
from mm_balance.config import Config
from mm_balance.price import Prices
from mm_balance.types import Coin


@dataclass
class Total:
    coins: dict[str, Decimal]
    coins_share: dict[str, Decimal]
    # usd_share: dict[str, Decimal]  # all stablecoins have key 'usd'
    usd_sum: Decimal  # sum of all coins in USD
    usd_sum_share: Decimal

    stablecoin_sum: Decimal  # sum of usd stablecoins: usdt, usdc
    stablecoin_sum_share: Decimal

    config: Config
    prices: Prices

    @classmethod
    def calc(cls, balances: Balances, prices: Prices, config: Config) -> Self:
        coins: dict[str, Decimal] = defaultdict(Decimal)
        coins_share: dict[str, Decimal] = defaultdict(Decimal)
        # usd_share: dict[str, Decimal] = defaultdict(Decimal)
        usd_sum = Decimal(0)
        usd_sum_share = Decimal(0)

        stablecoin_sum = Decimal(0)
        stablecoin_sum_share = Decimal(0)
        for group_index, group in enumerate(config.groups):
            balance_sum = Decimal(0)
            # for address_task in [t for t in tasks.network_tasks(group.network) if t.group_index == group_index]:
            for address_task in balances.get_group_balances(group_index, group.network):
                if isinstance(address_task.balance, Ok):
                    balance_sum += address_task.balance.ok
                    if group.coin in Coin.usd_coins():
                        stablecoin_sum += address_task.balance.ok
                        stablecoin_sum_share += address_task.balance.ok * group.share
                    if config.price:
                        balance_usd = round(address_task.balance.ok * prices[group.coin], config.round_ndigits)
                        usd_sum += balance_usd
                        usd_sum_share += group.share * balance_usd

            coins[group.coin] += balance_sum
            coins_share[group.coin] += round(balance_sum * group.share, config.round_ndigits)
        return cls(
            coins=coins,
            coins_share=coins_share,
            usd_sum=usd_sum,
            usd_sum_share=usd_sum_share,
            # usd_share=usd_share,
            stablecoin_sum=stablecoin_sum,
            stablecoin_sum_share=stablecoin_sum_share,
            config=config,
            prices=prices,
        )

    def print(self) -> None:
        if self.config.print_format == PrintFormat.TABLE:
            if self.config.price:
                self._print_total_total_with_price()
                self._print_share_total_with_price()
            else:
                self._print_total_total_without_price()
                self._print_share_total_without_price()

    def _print_total_total_with_price(self) -> None:
        if self.config.print_format == PrintFormat.TABLE:
            rows = []
            for key, value in self.coins.items():
                usd_value = round(value * self.prices[key], self.config.round_ndigits)
                if key in Coin.usd_coins():
                    usd_share = round(self.stablecoin_sum * 100 / self.usd_sum, self.config.round_ndigits)
                else:
                    usd_share = round(usd_value * 100 / self.usd_sum, self.config.round_ndigits)
                rows.append([key, value, usd_value, usd_share])
            rows.append(["usd_sum", self.usd_sum])
            print_table("total", ["coin", "balance", "usd", "usd_share"], rows)

    def _print_total_total_without_price(self) -> None:
        if self.config.print_format == PrintFormat.TABLE:
            rows = []
            for key, value in self.coins.items():
                rows.append([key, value])
            print_table("total", ["coin", "balance"], rows)

    def _print_share_total_with_price(self) -> None:
        rows = []
        for key, _ in self.coins.items():
            usd_value = round(self.coins_share[key] * self.prices[key], self.config.round_ndigits)
            if key in Coin.usd_coins():
                usd_share = round(self.stablecoin_sum_share * 100 / self.usd_sum_share, self.config.round_ndigits)
            else:
                usd_share = round(usd_value * 100 / self.usd_sum_share, self.config.round_ndigits)
            rows.append([key, self.coins_share[key], usd_value, usd_share])
        rows.append(["usd_sum", self.usd_sum_share])
        print_table("total / share", ["coin", "balance", "usd", "usd_share"], rows)

    def _print_share_total_without_price(self) -> None:
        rows = []
        for key, _ in self.coins.items():
            rows.append([key, self.coins_share[key]])
        print_table("total / share", ["coin", "balance"], rows)
