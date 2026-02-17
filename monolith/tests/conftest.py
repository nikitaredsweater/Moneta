"""
Pytest configuration and shared fixtures for monolith tests.

This conftest.py is automatically loaded by pytest and provides:
- Common fixtures for testing
- Test configuration
"""

import sys
from pathlib import Path

import pytest

# Add the monolith app directory to Python path for imports
monolith_root = Path(__file__).parent.parent
sys.path.insert(0, str(monolith_root))


# ============================================================================
# Validation Test Fixtures
# ============================================================================


@pytest.fixture
def future_date():
    """Provide a date that is guaranteed to be in the future."""
    from datetime import date, timedelta

    return date.today() + timedelta(days=30)


@pytest.fixture
def past_date():
    """Provide a date that is guaranteed to be in the past."""
    from datetime import date, timedelta

    return date.today() - timedelta(days=30)


@pytest.fixture
def valid_email():
    """Provide a valid email address for testing."""
    return "test.user@example.com"


@pytest.fixture
def valid_password():
    """Provide a valid password that meets requirements."""
    return "SecurePass123!"


# ============================================================================
# Filter Test Fixtures
# ============================================================================


@pytest.fixture
def sample_user_filters():
    """Provide sample UserFilters for testing."""
    from datetime import date

    from app.enums import UserRole
    from app.schemas.user import UserFilters

    return UserFilters(
        email="test",
        first_name="John",
        last_name="Doe",
        role=UserRole.BUYER,
        company_id=1,
        created_at_after=date(2024, 1, 1),
        created_at_before=date(2024, 12, 31),
    )


@pytest.fixture
def sample_company_filters():
    """Provide sample CompanyFilters for testing."""
    from datetime import date

    from app.schemas.company import CompanyFilters

    return CompanyFilters(
        legal_name="Acme",
        trade_name="Trading",
        registration_number="REG123",
        incorporation_date_after=date(2020, 1, 1),
        incorporation_date_before=date(2024, 12, 31),
        created_at_after=date(2024, 1, 1),
        created_at_before=date(2024, 12, 31),
    )


@pytest.fixture
def sample_instrument_filters():
    """Provide sample InstrumentFilters for testing."""
    from datetime import date

    from app.enums import InstrumentStatus, MaturityStatus, TradingStatus
    from app.schemas.instrument import InstrumentFilters

    return InstrumentFilters(
        min_face_value=1000.0,
        max_face_value=100000.0,
        currency="USD",
        maturity_date_after=date(2025, 1, 1),
        maturity_date_before=date(2026, 12, 31),
        instrument_status=InstrumentStatus.ACTIVE,
        maturity_status=MaturityStatus.NOT_DUE,
        trading_status=TradingStatus.OFF_MARKET,
        issuer_id=[1, 2, 3],
        created_by=[10, 20],
    )


@pytest.fixture
def empty_user_filters():
    """Provide empty UserFilters for testing."""
    from app.schemas.user import UserFilters

    return UserFilters()


@pytest.fixture
def empty_company_filters():
    """Provide empty CompanyFilters for testing."""
    from app.schemas.company import CompanyFilters

    return CompanyFilters()


@pytest.fixture
def empty_instrument_filters():
    """Provide empty InstrumentFilters for testing."""
    from app.schemas.instrument import InstrumentFilters

    return InstrumentFilters()
