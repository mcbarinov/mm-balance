from decimal import Decimal

from mm_std import Ok, print_table

from mm_balance.balances import Balances
from mm_balance.config import Config
from mm_balance.price import Prices
from mm_balance.total import Total


def print_groups(balances: Balances, config: Config, prices: Prices) -> None:
    for group_index, group in enumerate(config.groups):
        group_balances = balances.get_group_balances(group_index, group.network)
        _print_group(group, group_balances, config, prices)


def _print_group(group: Config.Group, group_balances: list[Balances.Balance], config: Config, prices: Prices) -> None:
    rows = []
    balance_sum = Decimal(0)
    usd_sum = Decimal(0)
    for address_task in group_balances:
        row = [address_task.address, address_task.balance.ok_or_err()]  # type: ignore[union-attr]
        if isinstance(address_task.balance, Ok):
            balance_sum += address_task.balance.ok
            if config.price:
                balance_usd = round(address_task.balance.ok * prices[group.coin], config.round_ndigits)
                usd_sum += balance_usd
                row.append(balance_usd)
        rows.append(row)

    sum_row = ["sum", round(balance_sum, config.round_ndigits)]
    if config.price:
        sum_row.append(round(usd_sum, config.round_ndigits))
    rows.append(sum_row)

    if group.share < Decimal(1):
        sum_share_row = [f"sum_share, {group.share}", round(balance_sum * group.share, config.round_ndigits)]
        if config.price:
            sum_share_row.append(round(usd_sum * group.share, config.round_ndigits))
        rows.append(sum_share_row)

    table_headers = ["address", "balance"]
    if config.price:
        table_headers += ["usd"]
    print_table(group.name, table_headers, rows)


def print_prices(config: Config, prices: Prices) -> None:
    if config.price:
        rows = [[k, round(v, config.round_ndigits)] for (k, v) in prices.items()]
        print_table("price", ["coin", "usd"], rows)


def print_total(config: Config, balances: Balances, prices: Prices) -> None:
    total = Total.calc(balances, prices, config)
    total.print()
