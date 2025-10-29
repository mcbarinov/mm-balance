import ast
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
    return round(Decimal(value / 10**decimals), round_ndigits)


def round_decimal(value: Decimal, round_ndigits: int) -> Decimal:
    if value == Decimal(0):
        return Decimal(0)
    return round(value, round_ndigits)


def _safe_eval_ast(node: ast.expr) -> Decimal:
    """Safely evaluate an AST node containing only arithmetic operations."""
    if isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float)):
            raise TypeError(f"Unsupported constant type: {type(node.value).__name__}")
        return Decimal(str(node.value))
    if isinstance(node, ast.BinOp):
        left = _safe_eval_ast(node.left)
        right = _safe_eval_ast(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        raise TypeError(f"Unsupported operation: {type(node.op).__name__}")
    if isinstance(node, ast.UnaryOp):
        operand = _safe_eval_ast(node.operand)
        if isinstance(node.op, ast.UAdd):
            return operand
        if isinstance(node.op, ast.USub):
            return -operand
        raise TypeError(f"Unsupported unary operation: {type(node.op).__name__}")
    raise TypeError(f"Unsupported node type: {type(node).__name__}")


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
        tree = ast.parse(expr, mode="eval")
        return _safe_eval_ast(tree.body)
    except Exception as e:
        raise ValueError(f"Invalid share expression '{expression}': {e}") from e


@unique
class PrintFormat(StrEnum):
    PLAIN = "plain"
    TABLE = "table"
    JSON = "json"
