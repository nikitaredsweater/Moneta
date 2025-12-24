"""
Integration test configuration and fixtures.

Provides database session fixtures and test client setup for integration tests.
Uses PostgreSQL test database (requires running PostgreSQL instance).

Configuration via environment variables:
    TEST_DATABASE_URL: Full PostgreSQL connection URL for tests
                       Default: postgresql+asyncpg://postgres:postgres@localhost:5432/moneta_test

Running locally:
    1. Ensure PostgreSQL is running
    2. Create test database: createdb moneta_test
    3. Run tests: pytest tests/integration/ -v

Running in Docker/CI:
    1. Set TEST_DATABASE_URL to point to your test database
    2. Example: TEST_DATABASE_URL=postgresql+asyncpg://user:pass@db-host:5432/test_db
    3. Run tests: pytest tests/integration/ -v

The test fixtures automatically:
    - Create all tables before each test
    - Drop all tables after each test
    - Rollback any uncommitted transactions
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Add app to path
monolith_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(monolith_root))

from app.enums import ActivationStatus, UserRole
from app.models.base import Base
from app.security import create_access_token

# Test database URL - Use PostgreSQL test database
# Set TEST_DATABASE_URL env var or use default local test database
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/moneta_test",
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a test database engine with PostgreSQL."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for a test."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def test_session_maker(test_engine):
    """Create a session maker for dependency injection override."""
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


def create_test_token(
    user_id: str,
    role: UserRole = UserRole.BUYER,
    company_id: str = None,
    account_status: ActivationStatus = ActivationStatus.ACTIVE,
) -> str:
    """
    Create a JWT token for testing.

    Args:
        user_id: The user ID to include in the token.
        role: The user role.
        company_id: The company ID (optional).
        account_status: The account status.

    Returns:
        A signed JWT token string.
    """
    return create_access_token(
        user_id=user_id,
        role=role,
        company_id=company_id,
        account_status=account_status,
    )


@pytest.fixture
def auth_headers():
    """Factory fixture for creating authorization headers."""

    def _create_headers(
        user_id: str,
        role: UserRole = UserRole.BUYER,
        company_id: str = None,
        account_status: ActivationStatus = ActivationStatus.ACTIVE,
    ) -> dict:
        token = create_test_token(
            user_id=user_id,
            role=role,
            company_id=company_id,
            account_status=account_status,
        )
        return {"Authorization": f"Bearer {token}"}

    return _create_headers


@pytest_asyncio.fixture(scope="function")
async def test_client(test_session_maker) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async test client with database session override.

    This fixture:
    1. Mocks JWT key loading to avoid file system dependencies
    2. Overrides the database session with the test session
    3. Provides an async HTTP client for testing endpoints
    """
    # Mock the JWT keys before importing the app
    mock_private_key = MagicMock()
    mock_public_key = MagicMock()

    with patch.dict(
        os.environ,
        {
            "JWT_PRIVATE_KEY_PATH": "/fake/path/private.pem",
            "JWT_PUBLIC_KEY_PATH": "/fake/path/public.pem",
        },
    ):
        with patch("moneta_auth.jwt_keys.load_keys"):
            with patch(
                "moneta_auth.jwt_keys.get_private_key",
                return_value=mock_private_key,
            ):
                with patch(
                    "moneta_auth.jwt_keys.get_public_key",
                    return_value=mock_public_key,
                ):
                    # Import app after mocking
                    from app.routers.v1.api import router as v1_router
                    from fastapi import FastAPI

                    # Create a minimal test app without the full lifespan
                    test_app = FastAPI()
                    test_app.include_router(v1_router, prefix="/v1")

                    # Override the session dependency
                    from app.utils.session import async_session

                    async def override_session():
                        async with test_session_maker() as session:
                            yield session

                    # Patch the session maker used by repositories
                    with patch(
                        "app.utils.session.async_session", test_session_maker
                    ):
                        transport = ASGITransport(app=test_app)
                        async with AsyncClient(
                            transport=transport, base_url="http://test"
                        ) as client:
                            yield client
