"""
Checks input fields of endpoints for some common validations
"""

from __future__ import annotations

import re
from datetime import date, datetime, timezone
from typing import Optional, Union
from app.exceptions import IncorrectInputFormatException

Number = Union[int, float]
DateLike = Union[date, datetime]

EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)


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

def ensure_valid_email(value: Optional[str], field_name: str) -> None:
    """
    Validate that a string field contains a properly formatted email address.

    Behavior:
      - If `value` is `None`, an error is raised (callers should omit the field
        for optional updates or handle None separately).
      - Validates using a regex pattern that checks for basic email format:
        local-part@domain.tld
      - The pattern allows common characters in the local part (letters, numbers,
        dots, underscores, percent, plus, hyphen).
      - Domain must have at least one dot and a valid TLD (2+ characters).

    Args:
        value: The candidate email string to validate.
        field_name: Logical field name to echo back in error messages.

    Raises:
        IncorrectInputFormatException: If `value` is `None`, not a string, or not
        a valid email format.

    Returns:
        None. (Raises on invalid input.)

    Examples:
        >>> ensure_valid_email("user@example.com", "email")  # OK
        >>> ensure_valid_email("test.email+tag@domain.co.uk", "email")  # OK
        >>> ensure_valid_email("invalid.email", "email")
        IncorrectInputFormatException: email must be a valid email address.
        >>> ensure_valid_email("@example.com", "email")
        IncorrectInputFormatException: email must be a valid email address.
    """
    if value is None:
        raise IncorrectInputFormatException(
            detail=f'{field_name} is required.',
        )
    
    if not isinstance(value, str):
        raise IncorrectInputFormatException(
            detail=f'{field_name} must be a string.',
        )
    
    # Strip whitespace and validate
    email = value.strip()
    
    if not email or not EMAIL_PATTERN.match(email):
        raise IncorrectInputFormatException(
            detail=f'{field_name} must be a valid email address.',
        )


def ensure_valid_password(value: Optional[str], field_name: str) -> None:
    """
    Validate that a password string meets minimum security requirements.

    Behavior:
      - If `value` is `None`, an error is raised (password is required).
      - Password must be at least 8 characters long.
      - Leading/trailing whitespace is stripped before validation.

    Args:
        value: The candidate password string to validate.
        field_name: Logical field name to echo back in error messages.

    Raises:
        IncorrectInputFormatException: If `value` is `None`, not a string, or
        doesn't meet minimum length requirement.

    Returns:
        None. (Raises on invalid input.)

    Examples:
        >>> ensure_valid_password("MySecurePass123", "password")  # OK
        >>> ensure_valid_password("12345678", "password")  # OK (meets length)
        >>> ensure_valid_password("short", "password")
        IncorrectInputFormatException: password must be at least 8 characters long.
        >>> ensure_valid_password("", "password")
        IncorrectInputFormatException: password must be at least 8 characters long.
    """
    if value is None:
        raise IncorrectInputFormatException(
            detail=f'{field_name} is required.',
        )
    
    if not isinstance(value, str):
        raise IncorrectInputFormatException(
            detail=f'{field_name} must be a string.',
        )
    
    # Strip whitespace for validation
    password = value.strip()
    
    if len(password) < 8:
        raise IncorrectInputFormatException(
            detail=f'{field_name} must be at least 8 characters long.',
        )

def ensure_not_empty(value: Optional[str], field_name: str) -> None:
    """
    Validate that a string field is not empty or whitespace-only.

    Behavior:
      - If `value` is `None`, an error is raised (field is required).
      - If `value` is not a string, an error is raised.
      - Leading/trailing whitespace is stripped before checking.
      - If the resulting string is empty, an error is raised.

    Args:
        value: The candidate string to validate.
        field_name: Logical field name to echo back in error messages.

    Raises:
        IncorrectInputFormatException: If `value` is `None`, not a string, or
        empty after stripping whitespace.

    Returns:
        None. (Raises on invalid input.)

    Examples:
        >>> ensure_not_empty("Hello", "username")  # OK
        >>> ensure_not_empty("  Valid  ", "username")  # OK (has content after strip)
        >>> ensure_not_empty("", "username")
        IncorrectInputFormatException: username cannot be empty.
        >>> ensure_not_empty("   ", "username")
        IncorrectInputFormatException: username cannot be empty.
        >>> ensure_not_empty(None, "username")
        IncorrectInputFormatException: username is required.
    """
    if value is None:
        raise IncorrectInputFormatException(
            detail=f'{field_name} is required.',
        )
    
    if not isinstance(value, str):
        raise IncorrectInputFormatException(
            detail=f'{field_name} must be a string.',
        )
    
    # Strip whitespace and check if empty
    if not value.strip():
        raise IncorrectInputFormatException(
            detail=f'{field_name} cannot be empty.',
        )