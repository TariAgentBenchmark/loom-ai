"""共享的积分精度工具方法。"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Union


DecimalInput = Union[str, int, float, Decimal]


_PRECISION = Decimal("0.01")


def to_decimal(value: DecimalInput) -> Decimal:
    """将任意输入转换为两位小数的 Decimal。"""

    if isinstance(value, Decimal):
        decimal_value = value
    else:
        decimal_value = Decimal(str(value))

    return decimal_value.quantize(_PRECISION, rounding=ROUND_HALF_UP)


def add(lhs: DecimalInput, rhs: DecimalInput) -> Decimal:
    """对两个积分值求和并保持精度。"""

    return (to_decimal(lhs) + to_decimal(rhs)).quantize(_PRECISION, rounding=ROUND_HALF_UP)


def subtract(lhs: DecimalInput, rhs: DecimalInput) -> Decimal:
    """积分相减并保持精度。"""

    return (to_decimal(lhs) - to_decimal(rhs)).quantize(_PRECISION, rounding=ROUND_HALF_UP)


def multiply(lhs: DecimalInput, rhs: DecimalInput) -> Decimal:
    """积分乘法（如数量计算）并保持精度。"""

    return (to_decimal(lhs) * to_decimal(rhs)).quantize(_PRECISION, rounding=ROUND_HALF_UP)


def to_float(value: DecimalInput) -> float:
    """转换为 float 以便序列化（前端展示）。"""

    return float(to_decimal(value))


