"""
Float precision utilities for tolerance-based comparisons and rounding.

This module provides functions for comparing and rounding float values with
epsilon-based tolerance to avoid floating-point precision errors. The standard
tolerance (epsilon) is 1e-6, matching the 6-decimal precision standard used
throughout the system.

**Why tolerance-based comparisons:**
Floating-point arithmetic can produce values like 99.999999 when 100.0 is expected
due to division operations. Direct equality (==) would fail, but tolerance-based
comparison treats these as equal.

**Standard epsilon:** 1e-6 (absolute tolerance, not relative)

**Exports:**
    - float_equals: Tolerance-based equality
    - float_less_than: Tolerance-based less-than
    - float_greater_than: Tolerance-based greater-than
    - float_gte: Convenience for >= with tolerance
    - float_lte: Convenience for <= with tolerance
    - round_float: Config-driven rounding

**Usage examples:**
```
from utils.float_precision import float_equals, float_gte, round_float

# Comparison
if float_equals(calculated_qty, expected_qty):
    # Quantities match within tolerance
    pass

# Convenience comparisons
if float_gte(completed, planned):
    # Job is complete
    pass

# Rounding for display or storage
clean_value = round_float(1/3)  # Returns 0.333333 (6 decimals)
```
"""

import math
from utils.config import get_config


def float_equals(a: float, b: float, epsilon: float = 1e-6) -> bool:
    """
    Check if two float values are equal within a tolerance (epsilon).

    Uses absolute tolerance comparison to handle floating-point precision errors.
    This prevents bugs where calculated values like 99.999999 don't match expected
    values like 100.0 due to rounding errors in arithmetic operations.

    Args:
        a: First float value to compare
        b: Second float value to compare
        epsilon: Absolute tolerance for equality (default: 1e-6)

    Returns:
        True if |a - b| <= epsilon, False otherwise

    Edge cases:
        - NaN handling follows IEEE 754: NaN is not equal to anything including itself
        - float_equals(float('nan'), float('nan')) returns False
        - float_equals(float('nan'), 1.0) returns False

    Examples:
        >>> float_equals(100.0, 99.999999)
        True
        >>> float_equals(100.0, 100.1)
        False
        >>> float_equals(1/3, 0.333333)
        True
        >>> float_equals(float('nan'), float('nan'))
        False
    """
    # Handle NaN per IEEE 754: NaN != NaN
    if math.isnan(a) or math.isnan(b):
        return False

    return math.isclose(a, b, abs_tol=epsilon, rel_tol=0.0)


def float_less_than(a: float, b: float, epsilon: float = 1e-6) -> bool:
    """
    Check if float a is strictly less than float b, accounting for tolerance.

    Returns True only if a < b AND they are not equal within epsilon tolerance.
    This prevents false positives where 99.999999 would be considered less than
    100.0 even though they should be treated as equal.

    Args:
        a: First float value to compare
        b: Second float value to compare
        epsilon: Absolute tolerance for equality check (default: 1e-6)

    Returns:
        True if a < b and not float_equals(a, b), False otherwise

    Examples:
        >>> float_less_than(99.0, 100.0)
        True
        >>> float_less_than(99.999999, 100.0)
        False  # Treated as equal within tolerance
        >>> float_less_than(100.0, 100.1)
        True

    Common usage:
        # Check if quantity is insufficient (not just nearly sufficient)
        if float_less_than(available_qty, required_qty):
            raise InsufficientQuantityError()

        # Check if progress threshold not yet reached
        if float_less_than(current_progress, 100.0):
            # Still in progress
            pass
    """
    return a < b and not float_equals(a, b, epsilon)


def float_greater_than(a: float, b: float, epsilon: float = 1e-6) -> bool:
    """
    Check if float a is strictly greater than float b, accounting for tolerance.

    Returns True only if a > b AND they are not equal within epsilon tolerance.
    This prevents false positives where 100.000001 would be considered greater
    than 100.0 even though they should be treated as equal.

    Args:
        a: First float value to compare
        b: Second float value to compare
        epsilon: Absolute tolerance for equality check (default: 1e-6)

    Returns:
        True if a > b and not float_equals(a, b), False otherwise

    Examples:
        >>> float_greater_than(101.0, 100.0)
        True
        >>> float_greater_than(100.000001, 100.0)
        False  # Treated as equal within tolerance
        >>> float_greater_than(99.9, 100.0)
        False

    Common usage:
        # Check if quantity exceeds limit
        if float_greater_than(actual_qty, max_qty):
            raise QuantityExceededError()

        # Check if progress completed
        if float_greater_than(current_progress, 99.99):
            # Consider complete even if not exactly 100.0
            mark_complete()
    """
    return a > b and not float_equals(a, b, epsilon)


def float_gte(a: float, b: float, epsilon: float = 1e-6) -> bool:
    """
    Check if a is greater than or equal to b with tolerance.

    Convenience function equivalent to: float_greater_than(a, b) or float_equals(a, b)

    Args:
        a: First value
        b: Second value
        epsilon: Tolerance for comparison (default: 1e-6)

    Returns:
        True if a >= b within tolerance, False otherwise

    Examples:
        >>> float_gte(100.0, 99.999999)
        True
        >>> float_gte(99.5, 100.0)
        False
        >>> float_gte(100.0, 100.0)
        True

    Note: Use this for business logic like completion checks where
    values like 99.999999 should be considered >= 100.0
    """
    return float_greater_than(a, b, epsilon) or float_equals(a, b, epsilon)


def float_lte(a: float, b: float, epsilon: float = 1e-6) -> bool:
    """
    Check if a is less than or equal to b with tolerance.

    Convenience function equivalent to: float_less_than(a, b) or float_equals(a, b)

    Args:
        a: First value
        b: Second value
        epsilon: Tolerance for comparison (default: 1e-6)

    Returns:
        True if a <= b within tolerance, False otherwise

    Examples:
        >>> float_lte(99.999999, 100.0)
        True
        >>> float_lte(100.5, 100.0)
        False
        >>> float_lte(100.0, 100.0)
        True

    Note: Use this for validation logic where values within epsilon
    should be considered equal or less than the threshold.
    """
    return float_less_than(a, b, epsilon) or float_equals(a, b, epsilon)


def round_float(value: float, decimals: int = None) -> float:
    """
    Round a float value to specified decimal places.

    Uses the configured precision (float_precision_decimals) when decimals is None.
    This ensures consistent rounding across the system for database serialization,
    display formatting, and calculations.

    Args:
        value: Float value to round
        decimals: Number of decimal places (default: None, uses config value)

    Returns:
        Rounded float value

    Edge cases:
        - Infinity returns as-is (rounding infinity is undefined)
        - NaN returns as-is (rounding NaN is undefined)
        - No bounds checking (accepts any finite float Python supports)

    Examples:
        >>> round_float(1/3)
        0.333333  # Uses config default (6 decimals)
        >>> round_float(1/3, decimals=2)
        0.33
        >>> round_float(99.999999)
        100.0
        >>> round_float(float('inf'))
        inf

    Common usage:
        # Round quantity before database write
        clean_qty = round_float(calculated_qty)

        # Round progress percentage for display
        progress_display = round_float(progress_value, decimals=2)

        # Round measurement with custom precision
        measurement = round_float(sensor_reading, decimals=4)
    """
    if decimals is None:
        decimals = get_config().float_precision_decimals

    # Return infinity/NaN as-is
    if math.isinf(value) or math.isnan(value):
        return value

    return round(value, decimals)
