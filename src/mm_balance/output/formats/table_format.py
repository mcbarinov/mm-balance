from decimal import Decimal

from mm_std import print_table

from mm_balance.config import Config
from mm_balance.output.utils import format_number
from mm_balance.price import Prices
from mm_balance.result import BalancesResult, GroupResult, Total
from mm_balance.token_decimals import TokenDecimals
from mm_balance.workers import Workers


def print_nodes(config: Config) -> None:
    rows = []
    for network, nodes in config.nodes.items():
        rows.append([network, "\n".join(nodes)])
    print_table("Nodes", ["network", "nodes"], rows)


def print_token_decimals(token_decimals: TokenDecimals) -> None:
    rows = []
    for network, decimals in token_decimals.items():
        rows.append([network, decimals])
    print_table("Token Decimals", ["network", "decimals"], rows)


def print_prices(config: Config, prices: Prices) -> None:
    if config.price:
        rows = []
        for ticker, price in prices.items():
            rows.append([ticker, format_number(round(price, config.round_ndigits), config.format_number_separator, "$")])
        print_table("Prices", ["coin", "usd"], rows)


def print_result(config: Config, result: BalancesResult, workers: Workers) -> None:
    for group in result.groups:
        _print_group(config, group)

    _print_total(config, result.total, False)
    if config.has_share():
        _print_total(config, result.total_share, True)

    _print_errors(config, workers)


def _print_errors(config: Config, workers: Workers) -> None:
    error_tasks = workers.get_errors()
    if not error_tasks:
        return
    rows = []
    for task in error_tasks:
        group = config.groups[task.group_index]
        rows.append([group.ticker + " / " + group.network, task.wallet_address, task.balance.err])  # type: ignore[union-attr]
    print_table("Errors", ["coin", "address", "error"], rows)


def _print_total(config: Config, total: Total, is_share_total: bool) -> None:
    table_name = "Total, share" if is_share_total else "Total"
    headers = ["coin", "balance"]

    rows = []
    for ticker, balance in total.coin_balances.items():
        balance_str = format_number(balance, config.format_number_separator)
        row = [ticker, balance_str]
        if config.price:
            usd_value_str = format_number(total.coin_usd_values[ticker], config.format_number_separator, "$")
            portfolio_share = total.portfolio_share[ticker]
            row += [usd_value_str, f"{portfolio_share}%"]
        rows.append(row)

    if config.price:
        headers += ["usd", "portfolio_share"]
        if total.stablecoin_sum > 0:
            rows.append(["stablecoin_sum", format_number(total.stablecoin_sum, config.format_number_separator, "$")])
        rows.append(["total_usd_sum", format_number(total.total_usd_sum, config.format_number_separator, "$")])

    print_table(table_name, headers, rows)


def _print_group(config: Config, group: GroupResult) -> None:
    group_name = group.ticker
    if group.comment:
        group_name += " / " + group.comment
    group_name += " / " + group.network

    rows = []
    for address in group.addresses:
        if isinstance(address.balance, str):
            rows.append([address.address, address.balance])
        else:
            if config.skip_empty and address.balance.balance == Decimal(0):
                continue
            balance_str = format_number(address.balance.balance, config.format_number_separator)
            row = [address.address, balance_str]
            if config.price:
                usd_value_str = format_number(address.balance.usd_value, config.format_number_separator, "$")
                row.append(usd_value_str)
            rows.append(row)

    sum_row = ["sum", format_number(group.balance_sum, config.format_number_separator)]
    if config.price:
        sum_row.append(format_number(group.usd_sum, config.format_number_separator, "$"))
    rows.append(sum_row)

    if group.share < Decimal(1):
        sum_share_str = format_number(group.balance_sum_share, config.format_number_separator)
        sum_share_row = [f"sum_share, {group.share}", sum_share_str]
        if config.price:
            sum_share_row.append(format_number(group.usd_sum_share, config.format_number_separator, "$"))
        rows.append(sum_share_row)

    table_headers = ["address", "balance"]
    if config.price:
        table_headers += ["usd"]
    print_table(group_name, table_headers, rows)
