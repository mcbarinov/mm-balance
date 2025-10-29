from decimal import Decimal

import mm_print

from mm_balance.balance_fetcher import BalanceFetcher
from mm_balance.config import Config
from mm_balance.output.utils import format_number
from mm_balance.price import Prices
from mm_balance.result import BalancesResult, GroupResult, Total
from mm_balance.token_decimals import TokenDecimals


def print_nodes(config: Config) -> None:
    rows = []
    for network, nodes in config.nodes.items():
        rows.append([network, "\n".join(nodes)])
    mm_print.table(["network", "nodes"], rows, title="Nodes")


def print_proxy_count(config: Config) -> None:
    mm_print.table(["count"], [[len(config.settings.proxies)]], title="Proxies")


def print_token_decimals(token_decimals: TokenDecimals) -> None:
    rows = []
    for network, decimals in token_decimals.items():
        rows.append([network, decimals])
    mm_print.table(["network", "decimals"], rows, title="Token Decimals")


def print_prices(config: Config, prices: Prices) -> None:
    if config.settings.price:
        rows = []
        for ticker, price in prices.items():
            rows.append(
                [ticker, format_number(price, config.settings.format_number_separator, "$", config.settings.round_ndigits)]
            )
        mm_print.table(["coin", "usd"], rows, title="Prices")


def print_result(config: Config, result: BalancesResult, workers: BalanceFetcher) -> None:
    for group in result.groups:
        _print_group(config, group)

    _print_total(config, result.total, False)
    if config.has_share():
        _print_total(config, result.total_share, True)

    _print_errors(config, workers)


def _print_errors(config: Config, workers: BalanceFetcher) -> None:
    error_tasks = workers.get_errors()
    if not error_tasks:
        return
    rows = []
    for task in error_tasks:
        group = config.groups[task.group_index]
        rows.append([group.ticker + " / " + group.network, task.wallet_address, task.balance.error])  # type: ignore[union-attr]
    mm_print.table(["coin", "address", "error"], rows, title="Errors")


def _print_total(config: Config, total: Total, is_share_total: bool) -> None:
    table_name = "Total, share" if is_share_total else "Total"
    headers = ["coin", "balance"]

    rows = []
    for ticker, balance in total.coin_balances.items():
        balance_str = format_number(balance, config.settings.format_number_separator)
        row = [ticker, balance_str]
        if config.settings.price:
            usd_value_str = format_number(total.coin_usd_values[ticker], config.settings.format_number_separator, "$")
            portfolio_share = total.portfolio_share[ticker]
            row += [usd_value_str, f"{portfolio_share}%"]
        rows.append(row)

    if config.settings.price:
        headers += ["usd", "portfolio_share"]
        if total.stablecoin_sum > 0:
            rows.append(["stablecoin_sum", format_number(total.stablecoin_sum, config.settings.format_number_separator, "$")])
        rows.append(["total_usd_sum", format_number(total.total_usd_sum, config.settings.format_number_separator, "$")])

    mm_print.table(headers, rows, title=table_name)


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
            if config.settings.skip_empty and address.balance.balance == Decimal(0):
                continue
            balance_str = format_number(address.balance.balance, config.settings.format_number_separator)
            row = [address.address, balance_str]
            if config.settings.price:
                usd_value_str = format_number(address.balance.usd_value, config.settings.format_number_separator, "$")
                row.append(usd_value_str)
            rows.append(row)

    sum_row = ["sum", format_number(group.balance_sum, config.settings.format_number_separator)]
    if config.settings.price:
        sum_row.append(format_number(group.usd_sum, config.settings.format_number_separator, "$"))
    rows.append(sum_row)

    if group.share != "total":
        sum_share_str = format_number(group.balance_sum_share, config.settings.format_number_separator)
        sum_share_row = [f"sum_share, {group.share}", sum_share_str]
        if config.settings.price:
            sum_share_row.append(format_number(group.usd_sum_share, config.settings.format_number_separator, "$"))
        rows.append(sum_share_row)

    table_headers = ["address", "balance"]
    if config.settings.price:
        table_headers += ["usd"]
    mm_print.table(table_headers, rows, title=group_name)
