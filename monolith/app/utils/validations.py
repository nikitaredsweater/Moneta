"""
Checks input fields of endpoints for some common validations
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional, Union
from app.exceptions import IncorrectInputFormatException

Number = Union[int, float]
DateLike = Union[date, datetime]


def ensure_future(value: Optional[DateLike], field_name: str) -> None:
    """
    Validate that a date/datetime field represents a **future** calendar date.

    Behavior:
      - Accepts either `date` or `datetime`.
      - If `value` is a timezone-aware `datetime`, it is converted to UTC and the
        **date component** is compared to today's UTC date.
      - If `value` is a naive `datetime`, only its `.date()` component is used as-is.
      - If the resulting date is **today or in the past**, an error is raised.
      - If `value` is `None`, an error is raised (callers should omit the field instead
        for optional/partial updates).

    Args:
        value: The candidate value to validate (date or datetime).
        field_name: Logical field name to echo back in error messages.

    Raises:
        IncorrectInputFormatException: If `value` is `None`, not a valid future date,
        or otherwise fails the check.

    Returns:
        None. (Raises on invalid input.)

    Examples:
        >>> ensure_future(date.today() + timedelta(days=1), "maturity_date")  # OK
        >>> ensure_future(datetime.utcnow() + timedelta(days=1), "maturity_date")  # OK (aware/naive both accepted)
        >>> ensure_future(date.today(), "maturity_date")
        IncorrectInputFormatException: maturity_date must be a future date.
    """
    if value is None:
        raise IncorrectInputFormatException(
            detail=f'{field_name} must be a date.',
        )

    if isinstance(value, datetime):
        # Normalize to a UTC calendar date for comparison
        if value.tzinfo is None:
            as_date = value.date()
        else:
            as_date = value.astimezone(timezone.utc).date()
    else:
        as_date = value

    today = datetime.now(timezone.utc).date()
    if as_date <= today:
        raise IncorrectInputFormatException(
            detail=f'{field_name} must be a future date.',
        )


def ensure_positive(value: Optional[Number], field_name: str) -> None:
    """
    Validate that a numeric field is strictly **greater than 0**.

    Behavior:
      - If `value` is `None`, the function **returns without error** (useful for PATCH
        handlers where the field may be omitted).
      - Attempts to coerce the value to `float`; non-numeric inputs fail validation.
      - Values `<= 0` fail validation.

    Args:
        value: The candidate numeric value (int/float or coercible).
        field_name: Logical field name to echo back in error messages.

    Raises:
        IncorrectInputFormatException: If the value is non-numeric or not strictly positive.

    Returns:
        None. (Raises on invalid input.)

    Examples:
        >>> ensure_positive(1, "face_value")       # OK
        >>> ensure_positive(0.01, "face_value")    # OK
        >>> ensure_positive(0, "face_value")
        IncorrectInputFormatException: face_value must be > 0.
        >>> ensure_positive("abc", "face_value")
        IncorrectInputFormatException: face_value must be a number.
    """
    if value is None:
        return
    try:
        if float(value) <= 0:
            raise IncorrectInputFormatException(
                detail=f'{field_name} must be > 0.',
            )
    except (TypeError, ValueError):
        raise IncorrectInputFormatException(
            detail=f'{field_name} must be a number.',
        )