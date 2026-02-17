"""
Unit tests for app.utils.filters.user_filters module.

Tests the filter and sort building functions for User queries:
- build_where_user
- build_sort_user
"""

from datetime import date
from uuid import uuid4

import pytest
from app import models
from app.enums import UserRole
from app.schemas.user import UserFilters
from app.utils.filters.user_filters import (
    ALLOWED_SORT_COLUMNS_USER,
    build_sort_user,
    build_where_user,
)
from sqlalchemy import asc, desc

# Test UUIDs for use in filters
TEST_COMPANY_UUID = uuid4()
TEST_COMPANY_UUID_2 = uuid4()


class TestBuildSortUser:
    """Tests for build_sort_user function."""

    def test_empty_string_returns_empty_list(self):
        """Empty sort expression should return empty list."""
        result = build_sort_user("")
        assert result == []

    def test_none_returns_empty_list(self):
        """None sort expression should return empty list."""
        result = build_sort_user(None)
        assert result == []

    def test_single_ascending_sort(self):
        """Single ascending sort field should work."""
        result = build_sort_user("created_at")
        assert len(result) == 1
        # Check it's an ascending order clause
        assert result[0].compare(asc(models.User.created_at))

    def test_single_descending_sort(self):
        """Single descending sort field (with -) should work."""
        result = build_sort_user("-created_at")
        assert len(result) == 1
        assert result[0].compare(desc(models.User.created_at))

    def test_multiple_sort_fields(self):
        """Multiple sort fields should all be processed."""
        result = build_sort_user("-created_at,first_name")
        assert len(result) == 2
        assert result[0].compare(desc(models.User.created_at))
        assert result[1].compare(asc(models.User.first_name))

    def test_invalid_column_ignored(self):
        """Invalid column names should be silently ignored."""
        result = build_sort_user("invalid_column")
        assert result == []

    def test_mixed_valid_invalid_columns(self):
        """Mix of valid and invalid columns should only include valid ones."""
        result = build_sort_user("-created_at,invalid,email")
        assert len(result) == 2
        assert result[0].compare(desc(models.User.created_at))
        assert result[1].compare(asc(models.User.email))

    def test_whitespace_handling(self):
        """Whitespace around column names should be handled."""
        result = build_sort_user("  created_at  ,  -email  ")
        assert len(result) == 2

    def test_empty_token_ignored(self):
        """Empty tokens (from double commas) should be ignored."""
        result = build_sort_user("created_at,,email")
        assert len(result) == 2

    def test_all_allowed_columns(self):
        """All whitelisted columns should be sortable."""
        for col_name in ALLOWED_SORT_COLUMNS_USER.keys():
            result = build_sort_user(col_name)
            assert len(result) == 1, f"Column {col_name} should be sortable"

    def test_descending_all_allowed_columns(self):
        """All whitelisted columns should be sortable in descending order."""
        for col_name in ALLOWED_SORT_COLUMNS_USER.keys():
            result = build_sort_user(f"-{col_name}")
            assert len(result) == 1, f"Column -{col_name} should be sortable"


class TestBuildWhereUser:
    """Tests for build_where_user function."""

    def test_empty_filters_returns_empty_list(self):
        """Filters with no fields set should return empty list."""
        filters = UserFilters()
        result = build_where_user(filters)
        assert result == []

    def test_email_partial_match(self):
        """Email filter should create ILIKE condition."""
        filters = UserFilters(email="test")
        result = build_where_user(filters)
        assert len(result) == 1
        # The condition should be an ILIKE with %test%
        condition = result[0]
        # Check it's a binary expression involving email
        assert "email" in str(condition).lower()

    def test_first_name_partial_match(self):
        """First name filter should create ILIKE condition."""
        filters = UserFilters(first_name="john")
        result = build_where_user(filters)
        assert len(result) == 1
        condition = result[0]
        assert "first_name" in str(condition).lower()

    def test_last_name_partial_match(self):
        """Last name filter should create ILIKE condition."""
        filters = UserFilters(last_name="doe")
        result = build_where_user(filters)
        assert len(result) == 1
        condition = result[0]
        assert "last_name" in str(condition).lower()

    def test_role_exact_match(self):
        """Role filter should create exact match condition."""
        filters = UserFilters(role=UserRole.ADMIN)
        result = build_where_user(filters)
        assert len(result) == 1
        condition = result[0]
        assert "role" in str(condition).lower()

    def test_company_id_exact_match(self):
        """Company ID filter should create exact match condition."""
        filters = UserFilters(company_id=TEST_COMPANY_UUID)
        result = build_where_user(filters)
        assert len(result) == 1
        condition = result[0]
        assert "company_id" in str(condition).lower()

    def test_created_at_after(self):
        """Created at after filter should create >= condition."""
        filters = UserFilters(created_at_after=date(2024, 1, 1))
        result = build_where_user(filters)
        assert len(result) == 1
        condition = result[0]
        assert "created_at" in str(condition).lower()
        # Check for >= operator
        assert ">=" in str(condition)

    def test_created_at_before(self):
        """Created at before filter should create <= condition."""
        filters = UserFilters(created_at_before=date(2024, 12, 31))
        result = build_where_user(filters)
        assert len(result) == 1
        condition = result[0]
        assert "created_at" in str(condition).lower()
        # Check for <= operator
        assert "<=" in str(condition)

    def test_created_at_range(self):
        """Both created_at filters should create two conditions."""
        filters = UserFilters(
            created_at_after=date(2024, 1, 1),
            created_at_before=date(2024, 12, 31),
        )
        result = build_where_user(filters)
        assert len(result) == 2

    def test_multiple_filters_combined(self):
        """Multiple filters should all be included."""
        filters = UserFilters(
            email="test",
            first_name="john",
            role=UserRole.BUYER,
            company_id=TEST_COMPANY_UUID,
        )
        result = build_where_user(filters)
        assert len(result) == 4

    def test_all_filters_combined(self):
        """All filter fields should be included when set."""
        filters = UserFilters(
            email="test@example.com",
            first_name="john",
            last_name="doe",
            role=UserRole.SELLER,
            company_id=TEST_COMPANY_UUID_2,
            created_at_after=date(2024, 1, 1),
            created_at_before=date(2024, 12, 31),
        )
        result = build_where_user(filters)
        assert len(result) == 7

    def test_none_role_not_included(self):
        """None role should not add a filter condition."""
        filters = UserFilters(role=None)
        result = build_where_user(filters)
        assert len(result) == 0

    def test_none_company_id_not_included(self):
        """None company_id should not add a filter condition."""
        filters = UserFilters(company_id=None)
        result = build_where_user(filters)
        assert len(result) == 0

    def test_empty_email_not_included(self):
        """Empty email string should not add a filter condition (falsy)."""
        filters = UserFilters(email="")
        result = build_where_user(filters)
        # Empty string is falsy, so no condition added
        assert len(result) == 0

    def test_partial_match_is_case_insensitive(self):
        """Email/name filters should use ILIKE for case-insensitivity."""
        filters = UserFilters(email="TEST")
        result = build_where_user(filters)
        assert len(result) == 1
        # ILIKE is case-insensitive - SQLAlchemy may render as ilike or lower() LIKE lower()
        condition_str = str(result[0]).lower()
        assert "ilike" in condition_str or (
            "like" in condition_str and "lower" in condition_str
        )
