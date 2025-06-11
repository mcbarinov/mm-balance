from decimal import Decimal
from enum import StrEnum, unique


def fnumber(value: Decimal, separator: str, extra: str | None = None) -> str:
    str_value = f"{value:,}".replace(",", separator)
    if extra == "$":
        return "$" + str_value
    if extra == "%":
        return str_value + "%"
    return str_value


def scale_and_round(value: int, decimals: int, round_ndigits: int) -> Decimal:
    if value == 0:
        return Decimal(0)
    return round(Decimal(value / 10**decimals), round_ndigits)


def round_decimal(value: Decimal, round_ndigits: int) -> Decimal:
    if value == Decimal(0):
        return Decimal(0)
    return round(value, round_ndigits)


@unique
class PrintFormat(StrEnum):
    PLAIN = "plain"
    TABLE = "table"
    JSON = "json"
