"""
Factory functions for creating test data.

These factories create database entities following the Arrange-Act-Assert pattern.
Each factory creates a single entity and returns it for use in tests.
"""

from datetime import date, datetime
from typing import Optional
from uuid import uuid4

from app.enums import ActivationStatus, UserRole
from app.models.company import Company
from app.models.user import User
from app.security import encrypt_password
from sqlalchemy.ext.asyncio import AsyncSession


class CompanyFactory:
    """Factory for creating Company entities in the test database."""

    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        legal_name: Optional[str] = None,
        trade_name: Optional[str] = None,
        registration_number: Optional[str] = None,
        incorporation_date: Optional[date] = None,
    ) -> Company:
        """
        Create a Company entity in the database.

        Args:
            session: The async database session.
            legal_name: Company legal name (auto-generated if not provided).
            trade_name: Company trade name (optional).
            registration_number: Company registration number (auto-generated if not provided).
            incorporation_date: Date of incorporation (defaults to 2020-01-01).

        Returns:
            The created Company ORM model.
        """
        unique_suffix = uuid4().hex[:8]

        company = Company(
            id=uuid4(),
            legal_name=legal_name or f"Test Company {unique_suffix}",
            trade_name=trade_name,
            registration_number=registration_number or f"REG-{unique_suffix}",
            incorporation_date=incorporation_date or date(2020, 1, 1),
            created_at=datetime.utcnow(),
        )

        session.add(company)
        await session.flush()
        await session.refresh(company)
        return company


class UserFactory:
    """Factory for creating User entities in the test database."""

    @staticmethod
    async def create(
        session: AsyncSession,
        company: Company,
        *,
        email: Optional[str] = None,
        password: str = "TestPassword123!",
        first_name: str = "Test",
        last_name: str = "User",
        role: UserRole = UserRole.BUYER,
        account_status: ActivationStatus = ActivationStatus.ACTIVE,
    ) -> User:
        """
        Create a User entity in the database.

        Args:
            session: The async database session.
            company: The Company the user belongs to.
            email: User email (auto-generated if not provided).
            password: Plain text password (will be encrypted).
            first_name: User first name.
            last_name: User last name.
            role: User role (defaults to BUYER).
            account_status: Account status (defaults to ACTIVE).

        Returns:
            The created User ORM model.
        """
        unique_suffix = uuid4().hex[:8]

        user = User(
            id=uuid4(),
            email=email or f"test.user.{unique_suffix}@example.com",
            password=encrypt_password(password),
            first_name=first_name,
            last_name=last_name,
            company_id=company.id,
            role=role,
            account_status=account_status,
            created_at=datetime.utcnow(),
        )

        session.add(user)
        await session.flush()
        await session.refresh(user)
        return user

    @staticmethod
    async def create_admin(
        session: AsyncSession,
        company: Company,
        *,
        email: Optional[str] = None,
        password: str = "AdminPassword123!",
    ) -> User:
        """
        Create an admin User entity in the database.

        Args:
            session: The async database session.
            company: The Company the user belongs to.
            email: User email (auto-generated if not provided).
            password: Plain text password.

        Returns:
            The created admin User ORM model.
        """
        return await UserFactory.create(
            session,
            company,
            email=email,
            password=password,
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            account_status=ActivationStatus.ACTIVE,
        )

    @staticmethod
    async def create_inactive(
        session: AsyncSession,
        company: Company,
        *,
        email: Optional[str] = None,
        password: str = "TestPassword123!",
        account_status: ActivationStatus = ActivationStatus.AWAITING_APPROVAL,
    ) -> User:
        """
        Create an inactive User entity in the database.

        Args:
            session: The async database session.
            company: The Company the user belongs to.
            email: User email (auto-generated if not provided).
            password: Plain text password.
            account_status: The inactive account status.

        Returns:
            The created inactive User ORM model.
        """
        return await UserFactory.create(
            session,
            company,
            email=email,
            password=password,
            first_name="Inactive",
            last_name="User",
            role=UserRole.BUYER,
            account_status=account_status,
        )
