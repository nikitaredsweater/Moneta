"""
Unit tests for app.utils.filters.instrument_filters module.

Tests the filter and sort building functions for Instrument queries:
- build_where_instrument
- build_sort_instrument
"""

from datetime import date
from uuid import uuid4

import pytest
from app import models
from app.enums import InstrumentStatus, MaturityStatus, TradingStatus
from app.schemas.instrument import InstrumentFilters
from app.utils.filters.instrument_filters import (
    ALLOWED_SORT_COLUMNS,
    build_sort_instrument,
    build_where_instrument,
)
from sqlalchemy import asc, desc

# Test UUIDs for use in filters
TEST_ISSUER_UUID_1 = uuid4()
TEST_ISSUER_UUID_2 = uuid4()
TEST_ISSUER_UUID_3 = uuid4()
TEST_CREATOR_UUID_1 = uuid4()
TEST_CREATOR_UUID_2 = uuid4()
TEST_CREATOR_UUID_3 = uuid4()


class TestBuildSortInstrument:
    """Tests for build_sort_instrument function."""

    def test_empty_string_returns_empty_list(self):
        """Empty sort expression should return empty list."""
        result = build_sort_instrument("")
        assert result == []

    def test_none_returns_empty_list(self):
        """None sort expression should return empty list."""
        result = build_sort_instrument(None)
        assert result == []

    def test_single_ascending_sort(self):
        """Single ascending sort field should work."""
        result = build_sort_instrument("created_at")
        assert len(result) == 1
        assert result[0].compare(asc(models.Instrument.created_at))

    def test_single_descending_sort(self):
        """Single descending sort field (with -) should work."""
        result = build_sort_instrument("-created_at")
        assert len(result) == 1
        assert result[0].compare(desc(models.Instrument.created_at))

    def test_multiple_sort_fields(self):
        """Multiple sort fields should all be processed."""
        result = build_sort_instrument("-created_at,name")
        assert len(result) == 2
        assert result[0].compare(desc(models.Instrument.created_at))
        assert result[1].compare(asc(models.Instrument.name))

    def test_invalid_column_ignored(self):
        """Invalid column names should be silently ignored."""
        result = build_sort_instrument("invalid_column")
        assert result == []

    def test_mixed_valid_invalid_columns(self):
        """Mix of valid and invalid columns should only include valid ones."""
        result = build_sort_instrument("-created_at,invalid,name")
        assert len(result) == 2

    def test_whitespace_handling(self):
        """Whitespace around column names should be handled."""
        result = build_sort_instrument("  created_at  ,  -name  ")
        assert len(result) == 2

    def test_empty_token_ignored(self):
        """Empty tokens (from double commas) should be ignored."""
        result = build_sort_instrument("created_at,,name")
        assert len(result) == 2

    def test_all_allowed_columns(self):
        """All whitelisted columns should be sortable."""
        for col_name in ALLOWED_SORT_COLUMNS.keys():
            result = build_sort_instrument(col_name)
            assert len(result) == 1, f"Column {col_name} should be sortable"

    def test_descending_all_allowed_columns(self):
        """All whitelisted columns should be sortable in descending order."""
        for col_name in ALLOWED_SORT_COLUMNS.keys():
            result = build_sort_instrument(f"-{col_name}")
            assert len(result) == 1, f"Column -{col_name} should be sortable"

    def test_sort_by_maturity_date(self):
        """Maturity date should be a valid sort column."""
        result = build_sort_instrument("maturity_date")
        assert len(result) == 1
        assert result[0].compare(asc(models.Instrument.maturity_date))

    def test_sort_by_face_value(self):
        """Face value should be a valid sort column."""
        result = build_sort_instrument("-face_value")
        assert len(result) == 1
        assert result[0].compare(desc(models.Instrument.face_value))

    def test_sort_by_maturity_payment(self):
        """Maturity payment should be a valid sort column."""
        result = build_sort_instrument("maturity_payment")
        assert len(result) == 1
        assert result[0].compare(asc(models.Instrument.maturity_payment))

    def test_sort_by_name(self):
        """Name should be a valid sort column."""
        result = build_sort_instrument("-name")
        assert len(result) == 1
        assert result[0].compare(desc(models.Instrument.name))


class TestBuildWhereInstrument:
    """Tests for build_where_instrument function."""

    def test_empty_filters_returns_empty_list(self):
        """Filters with no fields set should return empty list."""
        filters = InstrumentFilters()
        result = build_where_instrument(filters)
        assert result == []

    # Numeric range filters
    def test_min_face_value(self):
        """Min face value filter should create >= condition."""
        filters = InstrumentFilters(min_face_value=1000.0)
        result = build_where_instrument(filters)
        assert len(result) == 1
        condition = result[0]
        assert "face_value" in str(condition).lower()
        assert ">=" in str(condition)

    def test_max_face_value(self):
        """Max face value filter should create <= condition."""
        filters = InstrumentFilters(max_face_value=10000.0)
        result = build_where_instrument(filters)
        assert len(result) == 1
        condition = result[0]
        assert "face_value" in str(condition).lower()
        assert "<=" in str(condition)

    def test_face_value_range(self):
        """Both face value filters should create two conditions."""
        filters = InstrumentFilters(
            min_face_value=1000.0, max_face_value=10000.0
        )
        result = build_where_instrument(filters)
        assert len(result) == 2

    def test_min_maturity_payment(self):
        """Min maturity payment filter should create >= condition."""
        filters = InstrumentFilters(min_maturity_payment=500.0)
        result = build_where_instrument(filters)
        assert len(result) == 1
        condition = result[0]
        assert "maturity_payment" in str(condition).lower()
        assert ">=" in str(condition)

    def test_max_maturity_payment(self):
        """Max maturity payment filter should create <= condition."""
        filters = InstrumentFilters(max_maturity_payment=5000.0)
        result = build_where_instrument(filters)
        assert len(result) == 1
        condition = result[0]
        assert "maturity_payment" in str(condition).lower()
        assert "<=" in str(condition)

    def test_maturity_payment_range(self):
        """Both maturity payment filters should create two conditions."""
        filters = InstrumentFilters(
            min_maturity_payment=500.0, max_maturity_payment=5000.0
        )
        result = build_where_instrument(filters)
        assert len(result) == 2

    # Exact match filters
    def test_currency_exact_match(self):
        """Currency filter should create exact match condition."""
        filters = InstrumentFilters(currency="USD")
        result = build_where_instrument(filters)
        assert len(result) == 1
        condition = result[0]
        assert "currency" in str(condition).lower()

    def test_instrument_status_exact_match(self):
        """Instrument status filter should create exact match condition."""
        filters = InstrumentFilters(instrument_status=InstrumentStatus.ACTIVE)
        result = build_where_instrument(filters)
        assert len(result) == 1
        condition = result[0]
        assert "instrument_status" in str(condition).lower()

    def test_maturity_status_exact_match(self):
        """Maturity status filter should create exact match condition."""
        filters = InstrumentFilters(maturity_status=MaturityStatus.DUE)
        result = build_where_instrument(filters)
        assert len(result) == 1
        condition = result[0]
        assert "maturity_status" in str(condition).lower()

    def test_trading_status_exact_match(self):
        """Trading status filter should create exact match condition."""
        filters = InstrumentFilters(trading_status=TradingStatus.LISTED)
        result = build_where_instrument(filters)
        assert len(result) == 1
        condition = result[0]
        assert "trading_status" in str(condition).lower()

    # Date range filters
    def test_maturity_date_after(self):
        """Maturity date after filter should create >= condition."""
        filters = InstrumentFilters(maturity_date_after=date(2025, 1, 1))
        result = build_where_instrument(filters)
        assert len(result) == 1
        condition = result[0]
        assert "maturity_date" in str(condition).lower()
        assert ">=" in str(condition)

    def test_maturity_date_before(self):
        """Maturity date before filter should create <= condition."""
        filters = InstrumentFilters(maturity_date_before=date(2025, 12, 31))
        result = build_where_instrument(filters)
        assert len(result) == 1
        condition = result[0]
        assert "maturity_date" in str(condition).lower()
        assert "<=" in str(condition)

    def test_maturity_date_range(self):
        """Both maturity_date filters should create two conditions."""
        filters = InstrumentFilters(
            maturity_date_after=date(2025, 1, 1),
            maturity_date_before=date(2025, 12, 31),
        )
        result = build_where_instrument(filters)
        assert len(result) == 2

    def test_created_at_after(self):
        """Created at after filter should create >= condition."""
        filters = InstrumentFilters(created_at_after=date(2024, 1, 1))
        result = build_where_instrument(filters)
        assert len(result) == 1
        condition = result[0]
        assert "created_at" in str(condition).lower()
        assert ">=" in str(condition)

    def test_created_at_before(self):
        """Created at before filter should create <= condition."""
        filters = InstrumentFilters(created_at_before=date(2024, 12, 31))
        result = build_where_instrument(filters)
        assert len(result) == 1
        condition = result[0]
        assert "created_at" in str(condition).lower()
        assert "<=" in str(condition)

    def test_created_at_range(self):
        """Both created_at filters should create two conditions."""
        filters = InstrumentFilters(
            created_at_after=date(2024, 1, 1),
            created_at_before=date(2024, 12, 31),
        )
        result = build_where_instrument(filters)
        assert len(result) == 2

    # Array (IN) filters
    def test_issuer_id_single(self):
        """Single issuer_id should create IN condition."""
        filters = InstrumentFilters(issuer_id=[TEST_ISSUER_UUID_1])
        result = build_where_instrument(filters)
        assert len(result) == 1
        condition = result[0]
        assert "issuer_id" in str(condition).lower()

    def test_issuer_id_multiple(self):
        """Multiple issuer_ids should create IN condition."""
        filters = InstrumentFilters(
            issuer_id=[
                TEST_ISSUER_UUID_1,
                TEST_ISSUER_UUID_2,
                TEST_ISSUER_UUID_3,
            ]
        )
        result = build_where_instrument(filters)
        assert len(result) == 1
        condition = result[0]
        assert "issuer_id" in str(condition).lower()
        # Check for IN operator
        assert "in_" in str(condition).lower() or "IN" in str(condition)

    def test_created_by_single(self):
        """Single created_by should create IN condition."""
        filters = InstrumentFilters(created_by=[TEST_CREATOR_UUID_1])
        result = build_where_instrument(filters)
        assert len(result) == 1
        condition = result[0]
        assert "created_by" in str(condition).lower()

    def test_created_by_multiple(self):
        """Multiple created_by should create IN condition."""
        filters = InstrumentFilters(
            created_by=[
                TEST_CREATOR_UUID_1,
                TEST_CREATOR_UUID_2,
                TEST_CREATOR_UUID_3,
            ]
        )
        result = build_where_instrument(filters)
        assert len(result) == 1
        condition = result[0]
        assert "created_by" in str(condition).lower()

    # Combined filters
    def test_multiple_filters_combined(self):
        """Multiple filters should all be included."""
        filters = InstrumentFilters(
            currency="USD",
            instrument_status=InstrumentStatus.ACTIVE,
            min_face_value=1000.0,
        )
        result = build_where_instrument(filters)
        assert len(result) == 3

    def test_all_filters_combined(self):
        """All filter fields should be included when set."""
        filters = InstrumentFilters(
            min_face_value=1000.0,
            max_face_value=100000.0,
            currency="EUR",
            maturity_date_after=date(2025, 1, 1),
            maturity_date_before=date(2026, 12, 31),
            created_at_after=date(2024, 1, 1),
            created_at_before=date(2024, 12, 31),
            min_maturity_payment=500.0,
            max_maturity_payment=50000.0,
            instrument_status=InstrumentStatus.PENDING_APPROVAL,
            maturity_status=MaturityStatus.NOT_DUE,
            trading_status=TradingStatus.OFF_MARKET,
            issuer_id=[TEST_ISSUER_UUID_1, TEST_ISSUER_UUID_2],
            created_by=[TEST_CREATOR_UUID_1, TEST_CREATOR_UUID_2],
        )
        result = build_where_instrument(filters)
        # 14 filter conditions expected
        assert len(result) == 14

    # Edge cases
    def test_empty_issuer_id_list_not_included(self):
        """Empty issuer_id list should not add a filter condition."""
        filters = InstrumentFilters(issuer_id=[])
        result = build_where_instrument(filters)
        # Empty list is falsy, so no condition added
        assert len(result) == 0

    def test_empty_created_by_list_not_included(self):
        """Empty created_by list should not add a filter condition."""
        filters = InstrumentFilters(created_by=[])
        result = build_where_instrument(filters)
        assert len(result) == 0

    def test_none_currency_not_included(self):
        """None currency should not add a filter condition."""
        filters = InstrumentFilters(currency=None)
        result = build_where_instrument(filters)
        assert len(result) == 0

    def test_none_status_not_included(self):
        """None status values should not add filter conditions."""
        filters = InstrumentFilters(
            instrument_status=None, maturity_status=None, trading_status=None
        )
        result = build_where_instrument(filters)
        assert len(result) == 0

    def test_zero_face_value_included(self):
        """Zero face value should be included (is not None)."""
        filters = InstrumentFilters(min_face_value=0.0)
        result = build_where_instrument(filters)
        # 0.0 is not None, so condition should be added
        assert len(result) == 1

    # Status enum values
    def test_all_instrument_statuses(self):
        """All instrument status enum values should be filterable."""
        for status in InstrumentStatus:
            filters = InstrumentFilters(instrument_status=status)
            result = build_where_instrument(filters)
            assert len(result) == 1

    def test_all_maturity_statuses(self):
        """All maturity status enum values should be filterable."""
        for status in MaturityStatus:
            filters = InstrumentFilters(maturity_status=status)
            result = build_where_instrument(filters)
            assert len(result) == 1

    def test_all_trading_statuses(self):
        """All trading status enum values should be filterable."""
        for status in TradingStatus:
            filters = InstrumentFilters(trading_status=status)
            result = build_where_instrument(filters)
            assert len(result) == 1
