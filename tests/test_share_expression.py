from decimal import Decimal

import pytest

from mm_balance.utils import evaluate_share_expression


def test_total_expression():
    """Test simple 'total' expression returns full balance."""
    assert evaluate_share_expression("total", Decimal(100)) == Decimal(100)
    assert evaluate_share_expression("total", Decimal("1234.56")) == Decimal("1234.56")
    assert evaluate_share_expression("total", Decimal(0)) == Decimal(0)


def test_percentage_expressions():
    """Test percentage-style expressions with implicit multiplication."""
    assert evaluate_share_expression("0.5total", Decimal(100)) == Decimal(50)
    assert evaluate_share_expression("0.1total", Decimal(1000)) == Decimal(100)
    assert evaluate_share_expression("0.25total", Decimal(200)) == Decimal(50)


def test_subtraction_expressions():
    """Test expressions with subtraction."""
    assert evaluate_share_expression("total - 100", Decimal(500)) == Decimal(400)
    assert evaluate_share_expression("total - 50.5", Decimal(200)) == Decimal("149.5")
    assert evaluate_share_expression("0.5total - 100", Decimal(1000)) == Decimal(400)


def test_parentheses_expressions():
    """Test expressions with parentheses and implicit multiplication."""
    assert evaluate_share_expression("0.5(total - 100)", Decimal(500)) == Decimal(200)
    assert evaluate_share_expression("0.5(total - 50.44)", Decimal(200)) == Decimal("74.78")
    assert evaluate_share_expression("(total - 1000)", Decimal(5000)) == Decimal(4000)


def test_addition_expressions():
    """Test expressions with addition."""
    assert evaluate_share_expression("total + 100", Decimal(500)) == Decimal(600)
    assert evaluate_share_expression("0.3total + 50", Decimal(100)) == Decimal(80)


def test_complex_expressions():
    """Test more complex mathematical expressions."""
    assert evaluate_share_expression("(total - 100) * 0.5", Decimal(500)) == Decimal(200)
    assert evaluate_share_expression("total / 2", Decimal(100)) == Decimal(50)
    assert evaluate_share_expression("2(total - 50)", Decimal(100)) == Decimal(100)


def test_nested_parentheses():
    """Test expressions with nested parentheses."""
    assert evaluate_share_expression("0.5((total - 100) + 50)", Decimal(500)) == Decimal(225)


def test_zero_balance():
    """Test expressions with zero balance."""
    assert evaluate_share_expression("total", Decimal(0)) == Decimal(0)
    assert evaluate_share_expression("0.5total", Decimal(0)) == Decimal(0)
    assert evaluate_share_expression("total - 100", Decimal(0)) == Decimal(-100)


def test_negative_results():
    """Test expressions that result in negative values."""
    assert evaluate_share_expression("total - 1000", Decimal(500)) == Decimal(-500)
    assert evaluate_share_expression("0.5total - 100", Decimal(100)) == Decimal(-50)


def test_invalid_characters():
    """Test that invalid characters are rejected."""
    with pytest.raises(ValueError, match="invalid characters"):
        evaluate_share_expression("total; import os", Decimal(100))

    with pytest.raises(ValueError, match="invalid characters"):
        evaluate_share_expression("__import__('os')", Decimal(100))

    with pytest.raises(ValueError, match="invalid characters"):
        evaluate_share_expression("total & 1", Decimal(100))


def test_invalid_syntax():
    """Test that invalid syntax is rejected."""
    with pytest.raises(ValueError, match="Invalid share expression"):
        evaluate_share_expression("total +", Decimal(100))

    with pytest.raises(ValueError, match="Invalid share expression"):
        evaluate_share_expression("(total", Decimal(100))

    with pytest.raises(ValueError, match="Invalid share expression"):
        evaluate_share_expression("total total", Decimal(100))
