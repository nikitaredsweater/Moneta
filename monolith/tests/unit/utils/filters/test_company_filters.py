"""
Unit tests for app.utils.filters.company_filters module.

Tests the filter and sort building functions for Company queries:
- build_where_company
- build_sort_company
"""

from datetime import date

import pytest
from app import models
from app.schemas.company import CompanyFilters
from app.utils.filters.company_filters import (
    ALLOWED_SORT_COLUMNS_COMPANY,
    build_sort_company,
    build_where_company,
)
from sqlalchemy import asc, desc


class TestBuildSortCompany:
    """Tests for build_sort_company function."""

    def test_empty_string_returns_empty_list(self):
        """Empty sort expression should return empty list."""
        result = build_sort_company("")
        assert result == []

    def test_none_returns_empty_list(self):
        """None sort expression should return empty list."""
        result = build_sort_company(None)
        assert result == []

    def test_single_ascending_sort(self):
        """Single ascending sort field should work."""
        result = build_sort_company("created_at")
        assert len(result) == 1
        assert result[0].compare(asc(models.Company.created_at))

    def test_single_descending_sort(self):
        """Single descending sort field (with -) should work."""
        result = build_sort_company("-created_at")
        assert len(result) == 1
        assert result[0].compare(desc(models.Company.created_at))

    def test_multiple_sort_fields(self):
        """Multiple sort fields should all be processed."""
        result = build_sort_company("-created_at,legal_name")
        assert len(result) == 2
        assert result[0].compare(desc(models.Company.created_at))
        assert result[1].compare(asc(models.Company.legal_name))

    def test_invalid_column_ignored(self):
        """Invalid column names should be silently ignored."""
        result = build_sort_company("invalid_column")
        assert result == []

    def test_mixed_valid_invalid_columns(self):
        """Mix of valid and invalid columns should only include valid ones."""
        result = build_sort_company("-created_at,invalid,legal_name")
        assert len(result) == 2

    def test_whitespace_handling(self):
        """Whitespace around column names should be handled."""
        result = build_sort_company("  created_at  ,  -legal_name  ")
        assert len(result) == 2

    def test_empty_token_ignored(self):
        """Empty tokens (from double commas) should be ignored."""
        result = build_sort_company("created_at,,legal_name")
        assert len(result) == 2

    def test_all_allowed_columns(self):
        """All whitelisted columns should be sortable."""
        for col_name in ALLOWED_SORT_COLUMNS_COMPANY.keys():
            result = build_sort_company(col_name)
            assert len(result) == 1, f"Column {col_name} should be sortable"

    def test_descending_all_allowed_columns(self):
        """All whitelisted columns should be sortable in descending order."""
        for col_name in ALLOWED_SORT_COLUMNS_COMPANY.keys():
            result = build_sort_company(f"-{col_name}")
            assert len(result) == 1, f"Column -{col_name} should be sortable"

    def test_sort_by_trade_name(self):
        """Trade name should be a valid sort column."""
        result = build_sort_company("trade_name")
        assert len(result) == 1
        assert result[0].compare(asc(models.Company.trade_name))

    def test_sort_by_registration_number(self):
        """Registration number should be a valid sort column."""
        result = build_sort_company("-registration_number")
        assert len(result) == 1
        assert result[0].compare(desc(models.Company.registration_number))

    def test_sort_by_incorporation_date(self):
        """Incorporation date should be a valid sort column."""
        result = build_sort_company("incorporation_date")
        assert len(result) == 1
        assert result[0].compare(asc(models.Company.incorporation_date))


class TestBuildWhereCompany:
    """Tests for build_where_company function."""

    def test_empty_filters_returns_empty_list(self):
        """Filters with no fields set should return empty list."""
        filters = CompanyFilters()
        result = build_where_company(filters)
        assert result == []

    def test_legal_name_partial_match(self):
        """Legal name filter should create ILIKE condition."""
        filters = CompanyFilters(legal_name="Acme")
        result = build_where_company(filters)
        assert len(result) == 1
        condition = result[0]
        assert "legal_name" in str(condition).lower()
        # Check it uses ILIKE - SQLAlchemy may render as ilike or lower() LIKE lower()
        condition_str = str(condition).lower()
        assert "ilike" in condition_str or (
            "like" in condition_str and "lower" in condition_str
        )

    def test_trade_name_partial_match(self):
        """Trade name filter should create ILIKE condition."""
        filters = CompanyFilters(trade_name="Trading")
        result = build_where_company(filters)
        assert len(result) == 1
        condition = result[0]
        assert "trade_name" in str(condition).lower()

    def test_registration_number_partial_match(self):
        """Registration number filter should create ILIKE condition."""
        filters = CompanyFilters(registration_number="REG123")
        result = build_where_company(filters)
        assert len(result) == 1
        condition = result[0]
        assert "registration_number" in str(condition).lower()

    def test_incorporation_date_after(self):
        """Incorporation date after filter should create >= condition."""
        filters = CompanyFilters(incorporation_date_after=date(2020, 1, 1))
        result = build_where_company(filters)
        assert len(result) == 1
        condition = result[0]
        assert "incorporation_date" in str(condition).lower()
        assert ">=" in str(condition)

    def test_incorporation_date_before(self):
        """Incorporation date before filter should create <= condition."""
        filters = CompanyFilters(incorporation_date_before=date(2024, 12, 31))
        result = build_where_company(filters)
        assert len(result) == 1
        condition = result[0]
        assert "incorporation_date" in str(condition).lower()
        assert "<=" in str(condition)

    def test_incorporation_date_range(self):
        """Both incorporation_date filters should create two conditions."""
        filters = CompanyFilters(
            incorporation_date_after=date(2020, 1, 1),
            incorporation_date_before=date(2024, 12, 31),
        )
        result = build_where_company(filters)
        assert len(result) == 2

    def test_created_at_after(self):
        """Created at after filter should create >= condition."""
        filters = CompanyFilters(created_at_after=date(2024, 1, 1))
        result = build_where_company(filters)
        assert len(result) == 1
        condition = result[0]
        assert "created_at" in str(condition).lower()
        assert ">=" in str(condition)

    def test_created_at_before(self):
        """Created at before filter should create <= condition."""
        filters = CompanyFilters(created_at_before=date(2024, 12, 31))
        result = build_where_company(filters)
        assert len(result) == 1
        condition = result[0]
        assert "created_at" in str(condition).lower()
        assert "<=" in str(condition)

    def test_created_at_range(self):
        """Both created_at filters should create two conditions."""
        filters = CompanyFilters(
            created_at_after=date(2024, 1, 1),
            created_at_before=date(2024, 12, 31),
        )
        result = build_where_company(filters)
        assert len(result) == 2

    def test_multiple_filters_combined(self):
        """Multiple filters should all be included."""
        filters = CompanyFilters(
            legal_name="Acme", trade_name="Trading", registration_number="REG"
        )
        result = build_where_company(filters)
        assert len(result) == 3

    def test_all_filters_combined(self):
        """All filter fields should be included when set."""
        filters = CompanyFilters(
            legal_name="Acme Corp",
            trade_name="Acme Trading",
            registration_number="REG12345",
            incorporation_date_after=date(2020, 1, 1),
            incorporation_date_before=date(2023, 12, 31),
            created_at_after=date(2024, 1, 1),
            created_at_before=date(2024, 12, 31),
        )
        result = build_where_company(filters)
        assert len(result) == 7

    def test_empty_legal_name_not_included(self):
        """Empty legal_name string should not add a filter condition."""
        filters = CompanyFilters(legal_name="")
        result = build_where_company(filters)
        assert len(result) == 0

    def test_empty_trade_name_not_included(self):
        """Empty trade_name string should not add a filter condition."""
        filters = CompanyFilters(trade_name="")
        result = build_where_company(filters)
        assert len(result) == 0

    def test_empty_registration_number_not_included(self):
        """Empty registration_number string should not add a filter condition."""
        filters = CompanyFilters(registration_number="")
        result = build_where_company(filters)
        assert len(result) == 0

    def test_none_dates_not_included(self):
        """None date values should not add filter conditions."""
        filters = CompanyFilters(
            incorporation_date_after=None,
            incorporation_date_before=None,
            created_at_after=None,
            created_at_before=None,
        )
        result = build_where_company(filters)
        assert len(result) == 0

    def test_partial_match_is_case_insensitive(self):
        """Text filters should use ILIKE for case-insensitivity."""
        filters = CompanyFilters(legal_name="ACME")
        result = build_where_company(filters)
        assert len(result) == 1
        # SQLAlchemy may render ILIKE as ilike or lower() LIKE lower()
        condition_str = str(result[0]).lower()
        assert "ilike" in condition_str or (
            "like" in condition_str and "lower" in condition_str
        )
