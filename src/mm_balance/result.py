from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from mm_std import Ok

from mm_balance.config import Config, Group
from mm_balance.constants import USD_STABLECOINS, Network
from mm_balance.price import Prices
from mm_balance.workers import Task, Workers


@dataclass
class Balance:
    balance: Decimal
    usd_value: Decimal  # 0 if config.price is False


@dataclass
class AddressBalance:
    address: str
    balance: Balance | str  # balance value or error message


@dataclass
class GroupResult:
    ticker: str
    network: Network
    comment: str
    share: Decimal
    addresses: list[AddressBalance]
    balance_sum: Decimal  # sum of all balances in the group
    usd_sum: Decimal  # sum of all usd values in the group
    balance_sum_share: Decimal  # sum of all balances in the group multiplied by share
    usd_sum_share: Decimal  # sum of all usd values in the group multiplied by share


@dataclass
class Total:
    coin_balances: dict[str, Decimal]
    coin_usd_values: dict[str, Decimal]
    portfolio_share: dict[str, Decimal]  # ticker -> usd value % from total usd value
    stablecoin_sum: Decimal  # sum of usd stablecoins: usdt, usdc, etc..
    total_usd_sum: Decimal  # sum of all coins in USD


@dataclass
class BalancesResult:
    groups: list[GroupResult]
    total: Total
    total_share: Total


def create_balances_result(config: Config, prices: Prices, workers: Workers) -> BalancesResult:
    groups = []
    for group_index, group in enumerate(config.groups):
        tasks = workers.get_group_tasks(group_index, group.network)
        groups.append(_create_group_result(config, group, tasks, prices))

    total = _create_total(False, groups)
    total_share = _create_total(True, groups)
    return BalancesResult(groups=groups, total=total, total_share=total_share)


def _create_total(use_share: bool, groups: list[GroupResult]) -> Total:
    coin_balances: dict[str, Decimal] = defaultdict(Decimal)  # ticker -> balance
    coin_usd_values: dict[str, Decimal] = defaultdict(Decimal)  # ticker -> usd value
    portfolio_share: dict[str, Decimal] = defaultdict(Decimal)  # ticker -> usd value % from total usd value
    total_usd_sum = Decimal(0)
    stablecoin_sum = Decimal(0)

    for group in groups:
        balance_value = group.balance_sum_share if use_share else group.balance_sum
        usd_value = group.usd_sum_share if use_share else group.usd_sum
        coin_balances[group.ticker] += balance_value
        coin_usd_values[group.ticker] += usd_value
        if group.ticker in USD_STABLECOINS:
            stablecoin_sum += usd_value  # TODO: or balance_value?
        total_usd_sum += usd_value

    if total_usd_sum > 0:
        for ticker, usd_value in coin_usd_values.items():
            if ticker in USD_STABLECOINS:
                portfolio_share[ticker] = round(stablecoin_sum * 100 / total_usd_sum, 2)
            else:
                portfolio_share[ticker] = round(usd_value * 100 / total_usd_sum, 2)

    return Total(
        coin_balances=coin_balances,
        coin_usd_values=coin_usd_values,
        portfolio_share=portfolio_share,
        stablecoin_sum=stablecoin_sum,
        total_usd_sum=total_usd_sum,
    )


def _create_group_result(config: Config, group: Group, tasks: list[Task], prices: Prices) -> GroupResult:
    addresses = []
    balance_sum = Decimal(0)
    usd_sum = Decimal(0)
    for task in tasks:
        balance: Balance | str
        if task.balance is None:
            balance = "balance is None! Something went wrong."
        else:
            if isinstance(task.balance, Ok):
                coin_value = task.balance.ok
                usd_value = Decimal(0)
                if group.ticker in prices:
                    usd_value = round(coin_value * prices[group.ticker], config.round_ndigits)
                balance = Balance(balance=coin_value, usd_value=usd_value)
                balance_sum += balance.balance
                usd_sum += balance.usd_value
            else:
                balance = task.balance.err
        addresses.append(AddressBalance(address=task.wallet_address, balance=balance))

    balance_sum_share = balance_sum * group.share
    usd_sum_share = usd_sum * group.share

    return GroupResult(
        ticker=group.ticker,
        network=group.network,
        comment=group.comment,
        share=group.share,
        addresses=addresses,
        balance_sum=balance_sum,
        usd_sum=usd_sum,
        balance_sum_share=balance_sum_share,
        usd_sum_share=usd_sum_share,
    )
