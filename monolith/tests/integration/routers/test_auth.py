"""
Integration tests for the Auth router (/v1/auth).

Tests the login endpoint with various scenarios:
- Successful login with valid credentials
- Failed login with invalid email
- Failed login with wrong password
- Failed login with inactive account
"""

import pytest
import pytest_asyncio
from app.enums import ActivationStatus, UserRole
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.factories import CompanyFactory, UserFactory


@pytest.mark.asyncio
class TestAuthLogin:
    """Tests for POST /v1/auth/login endpoint."""

    @pytest_asyncio.fixture
    async def company(self, db_session: AsyncSession):
        """Create a test company."""
        company = await CompanyFactory.create(db_session)
        await db_session.commit()
        return company

    @pytest_asyncio.fixture
    async def active_user(self, db_session: AsyncSession, company):
        """Create an active test user."""
        user = await UserFactory.create(
            db_session,
            company,
            email="active.user@example.com",
            password="ValidPassword123!",
            account_status=ActivationStatus.ACTIVE,
        )
        await db_session.commit()
        return user

    @pytest_asyncio.fixture
    async def inactive_user(self, db_session: AsyncSession, company):
        """Create an inactive test user."""
        user = await UserFactory.create_inactive(
            db_session,
            company,
            email="inactive.user@example.com",
            password="ValidPassword123!",
            account_status=ActivationStatus.AWAITING_APPROVAL,
        )
        await db_session.commit()
        return user

    async def test_login_success(
        self, test_client: AsyncClient, db_session: AsyncSession
    ):
        """
        Test successful login returns JWT token.

        Arrange: Create a company and an active user with known credentials.
        Act: POST to /v1/auth/login with valid email and password.
        Assert: Response is 200 with access_token, token_type, and expires.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        user = await UserFactory.create(
            db_session,
            company,
            email="login.success@example.com",
            password="ValidPassword123!",
            account_status=ActivationStatus.ACTIVE,
        )
        await db_session.commit()

        # Act
        response = await test_client.post(
            "/v1/auth/login",
            json={
                "email": "login.success@example.com",
                "password": "ValidPassword123!",
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires" in data
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    async def test_login_invalid_email_returns_401(
        self, test_client: AsyncClient, db_session: AsyncSession
    ):
        """
        Test login with non-existent email returns 401.

        Arrange: Create a company and user (but login with different email).
        Act: POST to /v1/auth/login with non-existent email.
        Assert: Response is 401 Unauthorized.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        user = await UserFactory.create(
            db_session,
            company,
            email="existing.user@example.com",
            password="ValidPassword123!",
        )
        await db_session.commit()

        # Act
        response = await test_client.post(
            "/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "ValidPassword123!",
            },
        )

        # Assert
        assert response.status_code == 401

    async def test_login_wrong_password_returns_401(
        self, test_client: AsyncClient, db_session: AsyncSession
    ):
        """
        Test login with wrong password returns 401.

        Arrange: Create a company and user with known password.
        Act: POST to /v1/auth/login with correct email but wrong password.
        Assert: Response is 401 Unauthorized.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        user = await UserFactory.create(
            db_session,
            company,
            email="wrong.password@example.com",
            password="CorrectPassword123!",
        )
        await db_session.commit()

        # Act
        response = await test_client.post(
            "/v1/auth/login",
            json={
                "email": "wrong.password@example.com",
                "password": "WrongPassword123!",
            },
        )

        # Assert
        assert response.status_code == 401

    async def test_login_inactive_account_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession
    ):
        """
        Test login with inactive account returns 403.

        Arrange: Create a company and user with AWAITING_APPROVAL status.
        Act: POST to /v1/auth/login with valid credentials.
        Assert: Response is 403 Forbidden (account not active).
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        user = await UserFactory.create_inactive(
            db_session,
            company,
            email="inactive.account@example.com",
            password="ValidPassword123!",
            account_status=ActivationStatus.AWAITING_APPROVAL,
        )
        await db_session.commit()

        # Act
        response = await test_client.post(
            "/v1/auth/login",
            json={
                "email": "inactive.account@example.com",
                "password": "ValidPassword123!",
            },
        )

        # Assert
        assert response.status_code == 403

    async def test_login_suspended_account_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession
    ):
        """
        Test login with suspended account returns 403.

        Arrange: Create a company and user with SUSPENDED status.
        Act: POST to /v1/auth/login with valid credentials.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        user = await UserFactory.create_inactive(
            db_session,
            company,
            email="suspended.account@example.com",
            password="ValidPassword123!",
            account_status=ActivationStatus.SUSPENDED,
        )
        await db_session.commit()

        # Act
        response = await test_client.post(
            "/v1/auth/login",
            json={
                "email": "suspended.account@example.com",
                "password": "ValidPassword123!",
            },
        )

        # Assert
        assert response.status_code == 403

    async def test_login_missing_email_returns_422(
        self, test_client: AsyncClient
    ):
        """
        Test login without email returns 422 validation error.

        Arrange: None (no database setup needed).
        Act: POST to /v1/auth/login without email field.
        Assert: Response is 422 Unprocessable Entity.
        """
        # Act
        response = await test_client.post(
            "/v1/auth/login",
            json={"password": "SomePassword123!"},
        )

        # Assert
        assert response.status_code == 422

    async def test_login_missing_password_returns_422(
        self, test_client: AsyncClient
    ):
        """
        Test login without password returns 422 validation error.

        Arrange: None (no database setup needed).
        Act: POST to /v1/auth/login without password field.
        Assert: Response is 422 Unprocessable Entity.
        """
        # Act
        response = await test_client.post(
            "/v1/auth/login",
            json={"email": "user@example.com"},
        )

        # Assert
        assert response.status_code == 422

    async def test_login_empty_body_returns_422(self, test_client: AsyncClient):
        """
        Test login with empty body returns 422 validation error.

        Arrange: None.
        Act: POST to /v1/auth/login with empty JSON body.
        Assert: Response is 422 Unprocessable Entity.
        """
        # Act
        response = await test_client.post(
            "/v1/auth/login",
            json={},
        )

        # Assert
        assert response.status_code == 422

    async def test_login_returns_valid_token_expiry(
        self, test_client: AsyncClient, db_session: AsyncSession
    ):
        """
        Test login returns token with expected expiry time.

        Arrange: Create a company and active user.
        Act: POST to /v1/auth/login with valid credentials.
        Assert: Response includes expires field with expected value (900 seconds = 15 min).
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        user = await UserFactory.create(
            db_session,
            company,
            email="token.expiry@example.com",
            password="ValidPassword123!",
        )
        await db_session.commit()

        # Act
        response = await test_client.post(
            "/v1/auth/login",
            json={
                "email": "token.expiry@example.com",
                "password": "ValidPassword123!",
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["expires"] == 900  # 15 minutes in seconds
