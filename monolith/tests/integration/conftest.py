"""
Integration test configuration and fixtures.

Provides database session fixtures and test client setup for integration tests.
Uses PostgreSQL test database (requires running PostgreSQL instance).

Configuration via environment variables:
    TEST_DATABASE_URL: Full PostgreSQL connection URL for tests (asyncpg format)
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
    - Run Alembic migrations to create tables (matching production schema)
    - Drop all tables after each test
    - Rollback any uncommitted transactions
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, patch

# Add app to path BEFORE any app imports
monolith_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(monolith_root))

# Test database URL - Use PostgreSQL test database
# Set TEST_DATABASE_URL env var or use default local test database
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/moneta_test",
)

# CRITICAL: Set DATABASE_URL environment variable BEFORE importing app modules
# This ensures that app.utils.session and conf.py use the test database
_sync_url = TEST_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
os.environ["DATABASE_URL"] = _sync_url

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.enums import ActivationStatus, UserRole
from app.models.base import Base
from app.security import create_access_token


def _get_sync_database_url() -> str:
    """
    Convert async database URL to sync format for Alembic.

    Alembic uses synchronous connections, so we need to convert
    asyncpg URLs to psycopg format.
    """
    return TEST_DATABASE_URL.replace(
        "postgresql+asyncpg://", "postgresql+psycopg://"
    )


def _run_alembic_migrations() -> None:
    """
    Run Alembic migrations to set up the test database schema.

    This ensures the test database matches the production schema exactly,
    including any data migrations or custom SQL in migration files.
    """
    sync_url = _get_sync_database_url()

    # Set DATABASE_URL for Alembic's conf.py to pick up
    env = os.environ.copy()
    env["DATABASE_URL"] = sync_url

    print(f"[TEST SETUP] Running Alembic migrations with DATABASE_URL: {sync_url}")

    # Run alembic upgrade head from the monolith root directory
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=str(monolith_root),
        env=env,
        capture_output=True,
        text=True,
    )

    print(f"[TEST SETUP] Alembic stdout: {result.stdout}")
    if result.stderr:
        print(f"[TEST SETUP] Alembic stderr: {result.stderr}")

    if result.returncode != 0:
        raise RuntimeError(
            f"Alembic migration failed (exit code {result.returncode}):\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    print("[TEST SETUP] Alembic migrations completed successfully")


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Track whether migrations have been run this session
_migrations_run = False


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """
    Create a test database engine with PostgreSQL.

    This fixture:
    1. Runs Alembic migrations once per session (matching production schema)
    2. Truncates all tables before each test for isolation
    3. Yields the engine for test use
    """
    global _migrations_run

    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    # Run Alembic migrations only once per session
    if not _migrations_run:
        # Drop all tables first to ensure clean state
        async with engine.begin() as conn:
            # Drop alembic_version table so migrations will run fresh
            await conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE;"))
            await conn.run_sync(Base.metadata.drop_all)

        # Run Alembic migrations
        _run_alembic_migrations()
        _migrations_run = True
    else:
        # Truncate all tables for test isolation (faster than drop/migrate)
        async with engine.begin() as conn:
            # Disable foreign key checks, truncate all tables, re-enable
            await conn.execute(text("SET session_replication_role = 'replica';"))
            for table in reversed(Base.metadata.sorted_tables):
                await conn.execute(text(f'TRUNCATE TABLE "{table.name}" CASCADE;'))
            await conn.execute(text("SET session_replication_role = 'origin';"))

    yield engine

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


def _generate_test_rsa_keys():
    """
    Generate RSA key pair for testing JWT token creation/verification.

    Returns a tuple of (private_key_pem, public_key_pem) as bytes.
    """
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend

    # Generate a 2048-bit RSA key pair
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )

    # Serialize private key to PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Serialize public key to PEM format
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    return private_pem, public_pem


# Generate test keys once at module load time
_TEST_PRIVATE_KEY, _TEST_PUBLIC_KEY = _generate_test_rsa_keys()


@pytest_asyncio.fixture(scope="function")
async def test_client(test_session_maker) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async test client with database session override.

    This fixture:
    1. Mocks JWT key manager with real test RSA keys for token creation/verification
    2. Uses the test database (DATABASE_URL set at module load time)
    3. Provides an async HTTP client for testing endpoints
    """
    # Create a mock JWTKeyManager with real RSA keys for testing
    mock_jwt_keys = MagicMock()
    mock_jwt_keys.private_key = _TEST_PRIVATE_KEY
    mock_jwt_keys.public_key = _TEST_PUBLIC_KEY
    mock_jwt_keys.can_sign = True
    mock_jwt_keys.can_verify = True
    mock_jwt_keys.is_loaded = True
    mock_jwt_keys.load_keys = MagicMock()
    mock_jwt_keys.load_public_key = MagicMock()
    mock_jwt_keys.load_private_key = MagicMock()

    # Patch jwt_keys in all locations where it's imported
    # The key location is moneta_auth.jwt.tokens where create_access_token uses it
    with patch("moneta_auth.jwt_keys", mock_jwt_keys):
        with patch("moneta_auth.jwt.jwt_keys", mock_jwt_keys):
            with patch("moneta_auth.jwt.keys.jwt_keys", mock_jwt_keys):
                with patch("moneta_auth.jwt.tokens.jwt_keys", mock_jwt_keys):
                    # Import app after mocking
                    from app.routers.v1.api import v1_router
                    from fastapi import FastAPI

                    # Create a minimal test app without the full lifespan
                    test_app = FastAPI()
                    test_app.include_router(v1_router, prefix="/v1")

                    transport = ASGITransport(app=test_app)
                    async with AsyncClient(
                        transport=transport, base_url="http://test"
                    ) as client:
                        yield client
