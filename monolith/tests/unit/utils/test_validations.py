"""
Unit tests for app.utils.validations module.

Tests all validation functions:
- ensure_future
- ensure_positive
- ensure_valid_email
- ensure_valid_password
- ensure_not_empty
"""

from datetime import date, datetime, timedelta, timezone

import pytest
from app.exceptions import IncorrectInputFormatException
from app.utils.validations import (
    ensure_future,
    ensure_not_empty,
    ensure_positive,
    ensure_valid_email,
    ensure_valid_password,
)


class TestEnsureFuture:
    """Tests for ensure_future validation function."""

    def test_future_date_passes(self):
        """A date in the future should pass validation."""
        future_date = date.today() + timedelta(days=1)
        # Should not raise
        ensure_future(future_date, "test_field")

    def test_future_date_far_future_passes(self):
        """A date far in the future should pass validation."""
        future_date = date.today() + timedelta(days=365)
        ensure_future(future_date, "test_field")

    def test_today_date_fails(self):
        """Today's date should fail validation (not strictly future)."""
        today = date.today()
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_future(today, "maturity_date")
        assert "maturity_date must be a future date" in str(
            exc_info.value.detail
        )

    def test_past_date_fails(self):
        """A past date should fail validation."""
        past_date = date.today() - timedelta(days=1)
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_future(past_date, "maturity_date")
        assert "maturity_date must be a future date" in str(
            exc_info.value.detail
        )

    def test_none_value_fails(self):
        """None value should fail validation."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_future(None, "maturity_date")
        assert "maturity_date must be a date" in str(exc_info.value.detail)

    def test_naive_datetime_future_passes(self):
        """A naive datetime in the future should pass validation."""
        future_dt = datetime.now() + timedelta(days=1)
        ensure_future(future_dt, "test_field")

    def test_naive_datetime_today_fails(self):
        """A naive datetime representing today should fail."""
        # Create a datetime that's definitely today
        today_dt = datetime.combine(date.today(), datetime.min.time())
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_future(today_dt, "test_field")
        assert "must be a future date" in str(exc_info.value.detail)

    def test_aware_datetime_future_passes(self):
        """A timezone-aware datetime in the future should pass validation."""
        future_dt = datetime.now(timezone.utc) + timedelta(days=1)
        ensure_future(future_dt, "test_field")

    def test_aware_datetime_past_fails(self):
        """A timezone-aware datetime in the past should fail."""
        past_dt = datetime.now(timezone.utc) - timedelta(days=1)
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_future(past_dt, "test_field")
        assert "must be a future date" in str(exc_info.value.detail)

    def test_field_name_in_error_message(self):
        """The field name should appear in the error message."""
        past_date = date.today() - timedelta(days=1)
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_future(past_date, "my_custom_field")
        assert "my_custom_field" in str(exc_info.value.detail)


class TestEnsurePositive:
    """Tests for ensure_positive validation function."""

    def test_positive_integer_passes(self):
        """A positive integer should pass validation."""
        ensure_positive(1, "face_value")
        ensure_positive(100, "face_value")
        ensure_positive(999999, "face_value")

    def test_positive_float_passes(self):
        """A positive float should pass validation."""
        ensure_positive(0.01, "face_value")
        ensure_positive(1.5, "face_value")
        ensure_positive(100.99, "face_value")

    def test_zero_fails(self):
        """Zero should fail validation (not strictly positive)."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_positive(0, "face_value")
        assert "face_value must be > 0" in str(exc_info.value.detail)

    def test_negative_integer_fails(self):
        """A negative integer should fail validation."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_positive(-1, "face_value")
        assert "face_value must be > 0" in str(exc_info.value.detail)

    def test_negative_float_fails(self):
        """A negative float should fail validation."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_positive(-0.01, "face_value")
        assert "face_value must be > 0" in str(exc_info.value.detail)

    def test_none_value_passes(self):
        """None value should pass (for PATCH handlers where field is optional)."""
        # Should not raise
        ensure_positive(None, "face_value")

    def test_non_numeric_string_fails(self):
        """A non-numeric string should fail validation."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_positive("abc", "face_value")
        assert "face_value must be a number" in str(exc_info.value.detail)

    def test_numeric_string_positive_passes(self):
        """A numeric string that's positive should pass (coerced to float)."""
        ensure_positive("10", "face_value")
        ensure_positive("0.5", "face_value")

    def test_numeric_string_zero_fails(self):
        """A numeric string representing zero should fail."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_positive("0", "face_value")
        assert "face_value must be > 0" in str(exc_info.value.detail)

    def test_field_name_in_error_message(self):
        """The field name should appear in the error message."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_positive(-5, "custom_amount")
        assert "custom_amount" in str(exc_info.value.detail)

    def test_very_small_positive_passes(self):
        """A very small positive number should pass."""
        ensure_positive(0.0001, "face_value")
        ensure_positive(1e-10, "face_value")


class TestEnsureValidEmail:
    """Tests for ensure_valid_email validation function."""

    def test_valid_simple_email_passes(self):
        """A simple valid email should pass."""
        ensure_valid_email("user@example.com", "email")

    def test_valid_email_with_subdomain_passes(self):
        """An email with subdomain should pass."""
        ensure_valid_email("user@mail.example.com", "email")

    def test_valid_email_with_plus_passes(self):
        """An email with plus sign should pass."""
        ensure_valid_email("user+tag@example.com", "email")

    def test_valid_email_with_dots_passes(self):
        """An email with dots in local part should pass."""
        ensure_valid_email("first.last@example.com", "email")

    def test_valid_email_with_numbers_passes(self):
        """An email with numbers should pass."""
        ensure_valid_email("user123@example.com", "email")
        ensure_valid_email("123user@example.com", "email")

    def test_valid_email_with_hyphen_domain_passes(self):
        """An email with hyphen in domain should pass."""
        ensure_valid_email("user@my-domain.com", "email")

    def test_valid_email_country_tld_passes(self):
        """An email with country code TLD should pass."""
        ensure_valid_email("user@example.co.uk", "email")
        ensure_valid_email("user@example.de", "email")

    def test_none_value_fails(self):
        """None value should fail validation."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_valid_email(None, "email")
        assert "email is required" in str(exc_info.value.detail)

    def test_empty_string_fails(self):
        """An empty string should fail validation."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_valid_email("", "email")
        assert "email must be a valid email address" in str(
            exc_info.value.detail
        )

    def test_whitespace_only_fails(self):
        """A whitespace-only string should fail validation."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_valid_email("   ", "email")
        assert "email must be a valid email address" in str(
            exc_info.value.detail
        )

    def test_missing_at_symbol_fails(self):
        """An email without @ symbol should fail."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_valid_email("userexample.com", "email")
        assert "email must be a valid email address" in str(
            exc_info.value.detail
        )

    def test_missing_domain_fails(self):
        """An email without domain should fail."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_valid_email("user@", "email")
        assert "email must be a valid email address" in str(
            exc_info.value.detail
        )

    def test_missing_local_part_fails(self):
        """An email without local part should fail."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_valid_email("@example.com", "email")
        assert "email must be a valid email address" in str(
            exc_info.value.detail
        )

    def test_missing_tld_fails(self):
        """An email without TLD should fail."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_valid_email("user@example", "email")
        assert "email must be a valid email address" in str(
            exc_info.value.detail
        )

    def test_single_char_tld_fails(self):
        """An email with single character TLD should fail."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_valid_email("user@example.c", "email")
        assert "email must be a valid email address" in str(
            exc_info.value.detail
        )

    def test_non_string_fails(self):
        """A non-string value should fail validation."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_valid_email(12345, "email")
        assert "email must be a string" in str(exc_info.value.detail)

    def test_field_name_in_error_message(self):
        """The field name should appear in the error message."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_valid_email("invalid", "user_email")
        assert "user_email" in str(exc_info.value.detail)

    def test_email_with_leading_trailing_spaces_passes(self):
        """An email with leading/trailing spaces should pass after stripping."""
        ensure_valid_email("  user@example.com  ", "email")


class TestEnsureValidPassword:
    """Tests for ensure_valid_password validation function."""

    def test_valid_password_8_chars_passes(self):
        """A password with exactly 8 characters should pass."""
        ensure_valid_password("12345678", "password")

    def test_valid_password_longer_passes(self):
        """A password longer than 8 characters should pass."""
        ensure_valid_password("MySecurePassword123!", "password")
        ensure_valid_password("a" * 100, "password")

    def test_short_password_fails(self):
        """A password shorter than 8 characters should fail."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_valid_password("short", "password")
        assert "password must be at least 8 characters long" in str(
            exc_info.value.detail
        )

    def test_7_char_password_fails(self):
        """A 7-character password should fail."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_valid_password("1234567", "password")
        assert "password must be at least 8 characters long" in str(
            exc_info.value.detail
        )

    def test_empty_password_fails(self):
        """An empty password should fail."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_valid_password("", "password")
        assert "password must be at least 8 characters long" in str(
            exc_info.value.detail
        )

    def test_none_value_fails(self):
        """None value should fail validation."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_valid_password(None, "password")
        assert "password is required" in str(exc_info.value.detail)

    def test_whitespace_only_fails(self):
        """A whitespace-only password should fail after stripping."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_valid_password("        ", "password")
        assert "password must be at least 8 characters long" in str(
            exc_info.value.detail
        )

    def test_non_string_fails(self):
        """A non-string value should fail validation."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_valid_password(12345678, "password")
        assert "password must be a string" in str(exc_info.value.detail)

    def test_password_with_spaces_passes(self):
        """A password with spaces in the middle should pass if long enough."""
        ensure_valid_password(
            "pass word", "password"
        )  # 9 chars including space

    def test_password_with_leading_trailing_spaces_stripped(self):
        """Leading/trailing spaces are stripped before length check."""
        # "  abc  " stripped is "abc" which is 3 chars - should fail
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_valid_password("  abc  ", "password")
        assert "password must be at least 8 characters long" in str(
            exc_info.value.detail
        )

    def test_field_name_in_error_message(self):
        """The field name should appear in the error message."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_valid_password("short", "user_password")
        assert "user_password" in str(exc_info.value.detail)


class TestEnsureNotEmpty:
    """Tests for ensure_not_empty validation function."""

    def test_non_empty_string_passes(self):
        """A non-empty string should pass validation."""
        ensure_not_empty("Hello", "username")
        ensure_not_empty("a", "username")

    def test_string_with_spaces_passes(self):
        """A string with content and spaces should pass."""
        ensure_not_empty("  Valid  ", "username")
        ensure_not_empty("Hello World", "username")

    def test_empty_string_fails(self):
        """An empty string should fail validation."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_not_empty("", "username")
        assert "username cannot be empty" in str(exc_info.value.detail)

    def test_whitespace_only_fails(self):
        """A whitespace-only string should fail validation."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_not_empty("   ", "username")
        assert "username cannot be empty" in str(exc_info.value.detail)

    def test_tabs_only_fails(self):
        """A string with only tabs should fail validation."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_not_empty("\t\t", "username")
        assert "username cannot be empty" in str(exc_info.value.detail)

    def test_newlines_only_fails(self):
        """A string with only newlines should fail validation."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_not_empty("\n\n", "username")
        assert "username cannot be empty" in str(exc_info.value.detail)

    def test_none_value_fails(self):
        """None value should fail validation."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_not_empty(None, "username")
        assert "username is required" in str(exc_info.value.detail)

    def test_non_string_fails(self):
        """A non-string value should fail validation."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_not_empty(123, "username")
        assert "username must be a string" in str(exc_info.value.detail)

    def test_list_fails(self):
        """A list should fail validation."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_not_empty(["a", "b"], "username")
        assert "username must be a string" in str(exc_info.value.detail)

    def test_field_name_in_error_message(self):
        """The field name should appear in the error message."""
        with pytest.raises(IncorrectInputFormatException) as exc_info:
            ensure_not_empty("", "company_name")
        assert "company_name" in str(exc_info.value.detail)

    def test_special_characters_pass(self):
        """Strings with special characters should pass."""
        ensure_not_empty("user@123", "username")
        ensure_not_empty("!@#$%", "username")
        ensure_not_empty("日本語", "username")
