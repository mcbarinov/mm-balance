import re
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
    return round(Decimal(value) / Decimal(10**decimals), round_ndigits)


def round_decimal(value: Decimal, round_ndigits: int) -> Decimal:
    if value == Decimal(0):
        return Decimal(0)
    return round(value, round_ndigits)


class _ExpressionParser:
    """Recursive descent parser for arithmetic expressions.

    Parses expressions by reading left-to-right, respecting operator precedence:
    1. Parentheses and unary +/- (highest)
    2. Multiplication and division
    3. Addition and subtraction (lowest)

    Uses self.pos as a cursor tracking current position in the string.
    """

    def __init__(self, expr: str) -> None:
        self.expr = expr.replace(" ", "")  # Expression string with spaces removed
        self.pos = 0  # Current position/index in the string (starts at beginning)

    def parse(self) -> Decimal:
        result = self._parse_expression()
        if self.pos < len(self.expr):
            raise ValueError(f"Unexpected character at position {self.pos}: '{self.expr[self.pos]}'")
        return result

    def _parse_expression(self) -> Decimal:
        """Parse addition and subtraction (lowest precedence)."""
        result = self._parse_term()

        while self.pos < len(self.expr):
            if self._peek() == "+":
                self.pos += 1
                result = result + self._parse_term()
            elif self._peek() == "-":
                self.pos += 1
                result = result - self._parse_term()
            else:
                break

        return result

    def _parse_term(self) -> Decimal:
        """Parse multiplication and division (medium precedence)."""
        result = self._parse_factor()

        while self.pos < len(self.expr):
            if self._peek() == "*":
                self.pos += 1
                result = result * self._parse_factor()
            elif self._peek() == "/":
                self.pos += 1
                divisor = self._parse_factor()
                if divisor == 0:
                    raise ValueError("Division by zero")
                result = result / divisor
            else:
                break

        return result

    def _parse_factor(self) -> Decimal:
        """Parse unary +/-, numbers, and parentheses (highest precedence)."""
        if self._peek() == "+":
            self.pos += 1
            return self._parse_factor()
        if self._peek() == "-":
            self.pos += 1
            return -self._parse_factor()

        if self._peek() == "(":
            self.pos += 1
            result = self._parse_expression()
            if self._peek() != ")":
                raise ValueError(f"Expected ')' at position {self.pos}")
            self.pos += 1
            return result

        return self._parse_number()

    def _parse_number(self) -> Decimal:
        """Parse a numeric value.

        Scans digits, optionally followed by a decimal point and more digits.
        Advances self.pos past the entire number.
        """
        start = self.pos

        # Scan integer part: consecutive digits
        while self.pos < len(self.expr) and self.expr[self.pos].isdigit():
            self.pos += 1

        # If there's a decimal point, scan fractional part
        if self.pos < len(self.expr) and self.expr[self.pos] == ".":
            self.pos += 1
            while self.pos < len(self.expr) and self.expr[self.pos].isdigit():
                self.pos += 1

        # Ensure we consumed at least one digit
        if start == self.pos:
            raise ValueError(f"Expected number at position {self.pos}")

        # Extract the substring from start to current position
        return Decimal(self.expr[start : self.pos])

    def _peek(self) -> str | None:
        """Peek at the current character without consuming it."""
        if self.pos < len(self.expr):
            return self.expr[self.pos]
        return None


def evaluate_share_expression(expression: str, balance_sum: Decimal) -> Decimal:
    """Evaluate share expression with actual balance_sum value.

    Supports expressions like:
    - "total" -> full balance
    - "0.5total" -> 50% of balance
    - "0.5(total - 100)" -> 50% of (balance - 100)
    - "total - 1000" -> balance minus 1000
    """
    if not re.match(r"^[0-9+\-*/.() total]+$", expression):
        raise ValueError(f"Invalid share expression '{expression}': contains invalid characters")

    # Insert * before ( when preceded by digit or )
    expr = re.sub(r"(\d|\))\(", r"\1*(", expression)
    # Insert * before 'total' when preceded by digit or )
    expr = re.sub(r"(\d|\))total", r"\1*total", expr)
    # Replace 'total' with actual value in parentheses
    expr = expr.replace("total", f"({balance_sum})")
    try:
        parser = _ExpressionParser(expr)
        return parser.parse()
    except Exception as e:
        raise ValueError(f"Invalid share expression '{expression}': {e}") from e


@unique
class PrintFormat(StrEnum):
    PLAIN = "plain"
    TABLE = "table"
    JSON = "json"
