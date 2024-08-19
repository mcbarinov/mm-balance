from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Self

from mm_std import Ok, PrintFormat, print_table

from mm_balance.balances import Balances
from mm_balance.config import Config
from mm_balance.types import Coin


@dataclass
class Total:
    coins: dict[str, Decimal]
    coins_ratio: dict[str, Decimal]
    usd_ratio: dict[str, Decimal]  # all stablecoins have key 'ust'
    usd_sum: Decimal  # sum of all coins in USD
    usd_sum_ratio: Decimal

    stablecoin_sum: Decimal  # sum of usd stablecoins: usdt, usdc, sdai
    stablecoin_sum_ratio: Decimal

    @classmethod
    def calc(cls, balances: Balances, prices: dict[str, Decimal], config: Config) -> Self:
        coins: dict[str, Decimal] = defaultdict(Decimal)
        coins_ratio: dict[str, Decimal] = defaultdict(Decimal)
        usd_ratio: dict[str, Decimal] = defaultdict(Decimal)
        usd_sum = Decimal(0)
        usd_sum_ratio = Decimal(0)

        stablecoin_sum = Decimal(0)
        stablecoin_sum_ratio = Decimal(0)
        for group_index, group in enumerate(config.groups):
            balance_sum = Decimal(0)
            # for address_task in [t for t in tasks.network_tasks(group.network) if t.group_index == group_index]:
            for address_task in balances.get_group_balances(group_index, group.network):
                if isinstance(address_task.balance, Ok):
                    balance_sum += address_task.balance.ok
                    if group.coin in Coin.usd_coins():
                        stablecoin_sum += address_task.balance.ok
                        stablecoin_sum_ratio += address_task.balance.ok * group.sum_ratio
                    if config.price:
                        balance_usd = round(address_task.balance.ok * prices[group.coin], config.round_ndigits)
                        usd_sum += balance_usd
                        usd_sum_ratio += group.sum_ratio * balance_usd

            coins[group.coin] += balance_sum
            coins_ratio[group.coin] += round(balance_sum * group.sum_ratio, config.round_ndigits)
        return cls(
            coins=coins,
            coins_ratio=coins_ratio,
            usd_sum=usd_sum,
            usd_sum_ratio=usd_sum_ratio,
            usd_ratio=usd_ratio,
            stablecoin_sum=stablecoin_sum,
            stablecoin_sum_ratio=stablecoin_sum_ratio,
        )

    def print(self, print_format: PrintFormat, prices: dict[str, Decimal], config: Config) -> None:
        if print_format == PrintFormat.TABLE:
            # print total total
            rows = []
            for key, value in self.coins.items():
                usd_value = round(value * prices[key], config.round_ndigits)
                if key in Coin.usd_coins():
                    usd_ratio = round(self.stablecoin_sum * 100 / self.usd_sum, config.round_ndigits)
                else:
                    usd_ratio = round(usd_value * 100 / self.usd_sum, config.round_ndigits)
                rows.append([key, value, usd_value, usd_ratio])
            rows.append(["usd_sum", self.usd_sum])
            print_table("total", ["coin", "balance", "usd", "usd_ratio"], rows)

            # print ratio total
            rows = []
            for key, _ in self.coins.items():
                usd_value = round(self.coins_ratio[key] * prices[key], config.round_ndigits)
                if key in Coin.usd_coins():
                    usd_ratio = round(self.stablecoin_sum_ratio * 100 / self.usd_sum_ratio, config.round_ndigits)
                else:
                    usd_ratio = round(usd_value * 100 / self.usd_sum_ratio, config.round_ndigits)
                rows.append([key, self.coins_ratio[key], usd_value, usd_ratio])
            rows.append(["usd_sum", self.usd_sum_ratio])
            print_table("total / ratio", ["coin", "balance", "usd", "usd_ratio"], rows)
