# ~/schematix/src/schematix/transforms/numbers.py
"""
Numeric transformation functions for mathematical operations and formatting.
"""
from __future__ import annotations
import re, decimal, math, typing as t

from schematix.core.transform import transform, Transform

# Type Conversion Classes

class to:
    """Type conversion transforms."""

    @transform
    @staticmethod
    def int(value: t.Any) -> int:
        """Convert value to integer."""
        if isinstance(value, str):
            # Handle common string formats
            cleaned = re.sub(r'[^\d+-]', '', value.strip())
            return int(cleaned) if cleaned and cleaned not in ['+', '-'] else 0
        return int(value)

    @transform
    @staticmethod
    def float(value: t.Any) -> float:
        """Convert value to float."""
        if isinstance(value, str):
            # Handle common string formats like "$1,234.56"
            cleaned = re.sub(r'[^\d+\-.e]', '', value.strip())
            return float(cleaned) if cleaned and cleaned not in ['+', '-', '.'] else 0.0
        return float(value)

    @transform
    @staticmethod
    def decimal(value: t.Any) -> decimal.Decimal:
        """Convert value to Decimal for precise decimal arithmetic."""
        if isinstance(value, str):
            # Clean string for decimal conversion
            cleaned = re.sub(r'[^\d+\-.]', '', value.strip())
            return decimal.Decimal(cleaned) if cleaned and cleaned not in ['+', '-', '.'] else decimal.Decimal('0')
        return decimal.Decimal(str(value))


class safeto:
    """Safe type conversion transforms with fallback defaults."""

    @staticmethod
    def int(default: int = 0) -> Transform:
        """
        Convert to integer with default fallback.

        Args:
            default: Value to return if conversion fails

        Returns:
            Transform that safely converts to int
        """
        @transform(name=f"safeto.int({default})")
        def _safetoint(value: t.Any) -> int:
            try:
                return to.int(value)
            except (ValueError, TypeError):
                return default
        return _safetoint

    @staticmethod
    def float(default: float = 0.0) -> Transform:
        """
        Convert to float with default fallback.

        Args:
            default: Value to return if conversion fails

        Returns:
            Transform that safely converts to float
        """
        @transform(name=f"safeto.float({default})")
        def _safetofloat(value: t.Any) -> float:
            try:
                return to.float(value)
            except (ValueError, TypeError):
                return default
        return _safetofloat


# Math Operations

@transform
def abs(value: t.Any) -> t.Union[int, float]:
    """Return absolute value."""
    import builtins
    return builtins.abs(to.float(value))

@transform
def negate(value: t.Any) -> t.Union[int, float]:
    """Return negative value."""
    return -to.float(value)

@transform
def reciprocal(value: t.Any) -> float:
    """Return reciprocal (1/x)."""
    num = to.float(value)
    if num == 0:
        raise ValueError("Cannot calculate reciprocal of zero")
    return 1.0 / num

def add(amount: t.Union[int, float]) -> Transform:
    """
    Add amount to value.

    Args:
        amount: Amount to add

    Returns:
        Transform that adds the amount
    """
    @transform(name=f"add({amount})")
    def _add(value: t.Any) -> t.Union[int, float]:
        return to.float(value) + amount
    return _add

def subtract(amount: t.Union[int, float]) -> Transform:
    """
    Subtract amount from value.

    Args:
        amount: Amount to subtract

    Returns:
        Transform that subtracts the amount
    """
    @transform(name=f"subtract({amount})")
    def _subtract(value: t.Any) -> t.Union[int, float]:
        return to.float(value) - amount
    return _subtract

def multiply(factor: t.Union[int, float]) -> Transform:
    """
    Multiply value by factor.

    Args:
        factor: Multiplication factor

    Returns:
        Transform that multiplies by factor
    """
    @transform(name=f"multiply({factor})")
    def _multiply(value: t.Any) -> t.Union[int, float]:
        return to.float(value) * factor
    return _multiply

def divide(divisor: t.Union[int, float]) -> Transform:
    """
    Divide value by divisor.

    Args:
        divisor: Division divisor

    Returns:
        Transform that divides by divisor
    """
    @transform(name=f"divide({divisor})")
    def _divide(value: t.Any) -> float:
        if divisor == 0:
            raise ValueError("Cannot divide by zero")
        return to.float(value) / divisor
    return _divide

def power(exponent: t.Union[int, float]) -> Transform:
    """
    Raise value to power.

    Args:
        exponent: Power exponent

    Returns:
        Transform that raises to power
    """
    @transform(name=f"power({exponent})")
    def _power(value: t.Any) -> float:
        return to.float(value) ** exponent
    return _power

def modulo(divisor: t.Union[int, float]) -> Transform:
    """
    Calculate modulo (remainder).

    Args:
        divisor: Modulo divisor

    Returns:
        Transform that calculates modulo
    """
    @transform(name=f"modulo({divisor})")
    def _modulo(value: t.Any) -> t.Union[int, float]:
        if divisor == 0:
            raise ValueError("Cannot calculate modulo with zero divisor")
        return to.float(value) % divisor
    return _modulo

# Rounding and Precision

def roundto(places: int = 0) -> Transform:
    """
    Round to specified decimal places.

    Args:
        places: Number of decimal places

    Returns:
        Transform that rounds to specified places
    """
    @transform(name=f"roundto({places})")
    def _roundto(value: t.Any) -> float:
        return round(to.float(value), places)
    return _roundto

@transform
def floor(value: t.Any) -> int:
    """Round down to nearest integer."""
    return math.floor(to.float(value))

@transform
def ceil(value: t.Any) -> int:
    """Round up to nearest integer."""
    return math.ceil(to.float(value))

@transform
def trunc(value: t.Any) -> int:
    """Truncate to integer (remove decimal part)."""
    return math.trunc(to.float(value))

# Range and Bounds

def clamp(minval: t.Union[int, float], maxval: t.Union[int, float]) -> Transform:
    """
    Clamp value to range [minval, maxval].

    Args:
        minval: Minimum value
        maxval: Maximum value

    Returns:
        Transform that clamps to range
    """
    @transform(name=f"clamp({minval}, {maxval})")
    def _clamp(value: t.Any) -> t.Union[int, float]:
        import builtins
        num = to.float(value)
        return builtins.max(minval, min(maxval, num))
    return _clamp

def minvalue(minimum: t.Union[int, float]) -> Transform:
    """
    Ensure value is at least minimum.

    Args:
        minimum: Minimum allowed value

    Returns:
        Transform that enforces minimum
    """
    @transform(name=f"minvalue({minimum})")
    def _minvalue(value: t.Any) -> t.Union[int, float]:
        import builtins
        return builtins.max(minimum, to.float(value))
    return _minvalue

def maxvalue(maximum: t.Union[int, float]) -> Transform:
    """
    Ensure value is at most maximum.

    Args:
        maximum: Maximum allowed value

    Returns:
        Transform that enforces maximum
    """
    @transform(name=f"maxvalue({maximum})")
    def _maxvalue(value: t.Any) -> t.Union[int, float]:
        import builtins
        return builtins.min(maximum, to.float(value))
    return _maxvalue

# Mathematical Functions

@transform
def sqrt(value: t.Any) -> float:
    """Calculate square root."""
    num = to.float(value)
    if num < 0:
        raise ValueError("Cannot calculate square root of negative number")
    return math.sqrt(num)

@transform
def log(value: t.Any) -> float:
    """Calculate natural logarithm."""
    num = to.float(value)
    if num <= 0:
        raise ValueError("Cannot calculate logarithm of non-positive number")
    return math.log(num)

def logbase(base: t.Union[int, float]) -> Transform:
    """
    Calculate logarithm with specified base.

    Args:
        base: Logarithm base

    Returns:
        Transform that calculates log with base
    """
    @transform(name=f"logbase({base})")
    def _logbase(value: t.Any) -> float:
        num = to.float(value)
        if num <= 0:
            raise ValueError("Cannot calculate logarithm of non-positive number")
        if base <= 0 or base == 1:
            raise ValueError("Invalid logarithm base")
        return math.log(num, base)
    return _logbase

@transform
def exp(value: t.Any) -> float:
    """Calculate e^x."""
    return math.exp(to.float(value))

@transform
def sin(value: t.Any) -> float:
    """Calculate sine (radians)."""
    return math.sin(to.float(value))

@transform
def cos(value: t.Any) -> float:
    """Calculate cosine (radians)."""
    return math.cos(to.float(value))

@transform
def tan(value: t.Any) -> float:
    """Calculate tangent (radians)."""
    return math.tan(to.float(value))

# Number Formatting

class format:
    """Number formatting utilities."""

    @staticmethod
    def currency(symbol: str = "$", places: int = 2) -> Transform:
        """
        Format as currency.

        Args:
            symbol: Currency symbol
            places: Decimal places

        Returns:
            Transform that formats as currency
        """
        @transform(name=f"format.currency({symbol}, {places})")
        def _currency(value: t.Any) -> str:
            num = to.float(value)
            return f"{symbol}{num:,.{places}f}"
        return _currency

    @staticmethod
    def percent(places: int = 1) -> Transform:
        """
        Format as percentage.

        Args:
            places: Decimal places

        Returns:
            Transform that formats as percentage
        """
        @transform(name=f"format.percent({places})")
        def _percent(value: t.Any) -> str:
            num = to.float(value) * 100
            return f"{num:.{places}f}%"
        return _percent

    @staticmethod
    def scientific(places: int = 2) -> Transform:
        """
        Format in scientific notation.

        Args:
            places: Decimal places

        Returns:
            Transform that formats in scientific notation
        """
        @transform(name=f"format.scientific({places})")
        def _scientific(value: t.Any) -> str:
            num = to.float(value)
            return f"{num:.{places}e}"
        return _scientific

    @staticmethod
    def commas(places: int = 2) -> Transform:
        """
        Format with comma separators.

        Args:
            places: Decimal places

        Returns:
            Transform that adds comma separators
        """
        @transform(name=f"format.commas({places})")
        def _commas(value: t.Any) -> str:
            num = to.float(value)
            return f"{num:,.{places}f}".rstrip('0').rstrip('.')
        return _commas

# Specialized Number Operations

@transform
def sign(value: t.Any) -> int:
    """Return sign of number (-1, 0, or 1)."""
    num = to.float(value)
    return -1 if num < 0 else 1 if num > 0 else 0

@transform
def factorial(value: t.Any) -> int:
    """Calculate factorial."""
    num = to.int(value)
    if num < 0:
        raise ValueError("Cannot calculate factorial of negative number")
    return math.factorial(num)

def gcd(other: int) -> Transform:
    """
    Calculate greatest common divisor.

    Args:
        other: Other number for GCD calculation

    Returns:
        Transform that calculates GCD
    """
    @transform(name=f"gcd({other})")
    def _gcd(value: t.Any) -> int:
        return math.gcd(to.int(value), other)
    return _gcd

@transform
def degrees(value: t.Any) -> float:
    """Convert radians to degrees."""
    return math.degrees(to.float(value))

@transform
def radians(value: t.Any) -> float:
    """Convert degrees to radians."""
    return math.radians(to.float(value))

# Utility Functions

@transform
def isinfinite(value: t.Any) -> bool:
    """Check if number is infinite."""
    return math.isinf(to.float(value))

@transform
def isnan(value: t.Any) -> bool:
    """Check if number is NaN."""
    return math.isnan(to.float(value))

@transform
def isfinite(value: t.Any) -> bool:
    """Check if number is finite."""
    return math.isfinite(to.float(value))

def inrange(minval: t.Union[int, float], maxval: t.Union[int, float], inclusive: bool = True) -> Transform:
    """
    Check if number is in range.

    Args:
        minval: Minimum value
        maxval: Maximum value
        inclusive: Whether bounds are inclusive

    Returns:
        Transform that checks if in range
    """
    @transform(name=f"inrange({minval}, {maxval})")
    def _inrange(value: t.Any) -> bool:
        num = to.float(value)
        if inclusive:
            return minval <= num <= maxval
        else:
            return minval < num < maxval
    return _inrange
