from decimal import Decimal


def fnumber(value: Decimal, separator: str, extra: str | None = None) -> str:
    str_value = f"{value:,}".replace(",", separator)
    if extra == "$":
        return "$" + str_value
    elif extra == "%":
        return str_value + "%"
    return str_value
