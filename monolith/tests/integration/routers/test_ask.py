"""
Integration tests for the Ask router (/v1/ask).

Tests ask CRUD operations with various scenarios:
- Search asks
- Get ask by ID
- Create ask
- Ask status transitions
- Update ask price/validity
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from app.enums import AskStatus, ExecutionMode, ListingStatus, UserRole
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.factories import (
    AskFactory,
    CompanyFactory,
    InstrumentFactory,
    InstrumentOwnershipFactory,
    ListingFactory,
    UserFactory,
)


class TestSearchAsks:
    """Tests for POST /v1/ask/search endpoint."""

    @pytest.mark.asyncio
    async def test_search_asks_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test search asks returns list of asks.

        Arrange: Create listing and asks.
        Act: POST /v1/ask/search with valid auth.
        Assert: Response is 200 with list of asks.
        """
        # Arrange
        seller_company = await CompanyFactory.create(
            db_session, legal_name="Seller Co"
        )
        seller_user = await UserFactory.create_issuer(
            db_session, seller_company
        )

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        await AskFactory.create_active(
            db_session, listing, seller_company, seller_user, amount=10000.00
        )
        await AskFactory.create_active(
            db_session, listing, seller_company, seller_user, amount=15000.00
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/ask/search",
            headers=headers,
            json={},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    @pytest.mark.asyncio
    async def test_search_asks_with_status_filter(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test search asks by status filter.

        Arrange: Create asks with different statuses.
        Act: POST /v1/ask/search with status filter.
        Assert: Response contains only asks with matching status.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(
            db_session, seller_company
        )

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        await AskFactory.create_active(
            db_session, listing, seller_company, seller_user
        )
        await AskFactory.create_withdrawn(
            db_session, listing, seller_company, seller_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/ask/search",
            headers=headers,
            json={"status": "ACTIVE"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        statuses = [ask["status"] for ask in data]
        assert all(s == "ACTIVE" for s in statuses)

    @pytest.mark.asyncio
    async def test_search_asks_non_owner_sees_only_active(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test that non-owner users can only see ACTIVE asks.

        Arrange: Create asks with various statuses.
        Act: POST /v1/ask/search as non-owner.
        Assert: Response contains only ACTIVE asks.
        """
        # Arrange
        seller_company = await CompanyFactory.create(
            db_session, legal_name="Seller Co"
        )
        other_company = await CompanyFactory.create(
            db_session, legal_name="Other Co"
        )
        seller_user = await UserFactory.create_issuer(
            db_session, seller_company
        )
        other_user = await UserFactory.create_issuer(db_session, other_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        await AskFactory.create_active(
            db_session, listing, seller_company, seller_user
        )
        await AskFactory.create_withdrawn(
            db_session, listing, seller_company, seller_user
        )
        await AskFactory.create_suspended(
            db_session, listing, seller_company, seller_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(other_user.id),
            role=UserRole.ISSUER,
            company_id=str(other_company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/ask/search",
            headers=headers,
            json={},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        statuses = [ask["status"] for ask in data]
        assert all(s == "ACTIVE" for s in statuses)

    @pytest.mark.asyncio
    async def test_search_asks_admin_sees_all(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test that ADMIN users can see all asks regardless of status.

        Arrange: Create asks with various statuses.
        Act: POST /v1/ask/search as ADMIN.
        Assert: Response contains all asks.
        """
        # Arrange
        seller_company = await CompanyFactory.create(
            db_session, legal_name="Seller Co"
        )
        admin_company = await CompanyFactory.create(
            db_session, legal_name="Admin Co"
        )
        seller_user = await UserFactory.create_issuer(
            db_session, seller_company
        )
        admin_user = await UserFactory.create_admin(db_session, admin_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        await AskFactory.create_active(
            db_session, listing, seller_company, seller_user
        )
        await AskFactory.create_withdrawn(
            db_session, listing, seller_company, seller_user
        )
        await AskFactory.create_suspended(
            db_session, listing, seller_company, seller_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin_user.id),
            role=UserRole.ADMIN,
            company_id=str(admin_company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/ask/search",
            headers=headers,
            json={},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3


class TestGetAskById:
    """Tests for GET /v1/ask/{ask_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_ask_by_id_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get ask by ID returns the ask.

        Arrange: Create an ask.
        Act: GET /v1/ask/{ask_id} with valid auth.
        Assert: Response is 200 with ask data.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(
            db_session, seller_company
        )

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        ask = await AskFactory.create_active(
            db_session, listing, seller_company, seller_user, amount=10000.00
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.get(
            f"/v1/ask/{ask.id}",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(ask.id)
        assert data["amount"] == 10000.00
        assert data["status"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_get_ask_not_found(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get ask by non-existent ID returns 404.

        Arrange: Create a user.
        Act: GET /v1/ask/{fake_id} with valid auth.
        Assert: Response is 404.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        user = await UserFactory.create_issuer(db_session, company)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(user.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )
        fake_uuid = str(uuid4())

        # Act
        response = await test_client.get(
            f"/v1/ask/{fake_uuid}",
            headers=headers,
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_non_active_ask_by_non_owner_returns_404(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test that non-owners cannot see non-ACTIVE asks.

        Arrange: Create a WITHDRAWN ask.
        Act: GET /v1/ask/{ask_id} as non-owner.
        Assert: Response is 404.
        """
        # Arrange
        seller_company = await CompanyFactory.create(
            db_session, legal_name="Seller Co"
        )
        other_company = await CompanyFactory.create(
            db_session, legal_name="Other Co"
        )
        seller_user = await UserFactory.create_issuer(
            db_session, seller_company
        )
        other_user = await UserFactory.create_issuer(db_session, other_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        ask = await AskFactory.create_withdrawn(
            db_session, listing, seller_company, seller_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(other_user.id),
            role=UserRole.ISSUER,
            company_id=str(other_company.id),
        )

        # Act
        response = await test_client.get(
            f"/v1/ask/{ask.id}",
            headers=headers,
        )

        # Assert
        assert response.status_code == 404


class TestCreateAsk:
    """Tests for POST /v1/ask endpoint."""

    @pytest.mark.asyncio
    async def test_create_ask_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create ask returns created ask.

        Arrange: Create a listing.
        Act: POST /v1/ask with valid data.
        Assert: Response is 200 with created ask.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(
            db_session, seller_company
        )

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/ask/",
            headers=headers,
            json={
                "listingId": str(listing.id),
                "amount": 10000.00,
                "currency": "USD",
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["listingId"] == str(listing.id)
        assert data["amount"] == 10000.00
        assert data["currency"] == "USD"
        assert data["status"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_create_ask_with_valid_until(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create ask with valid_until timestamp.

        Arrange: Create a listing.
        Act: POST /v1/ask with valid_until in the future.
        Assert: Response is 200 with valid_until set.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(
            db_session, seller_company
        )

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        future_date = (
            datetime.now(timezone.utc) + timedelta(days=30)
        ).isoformat()

        # Act
        response = await test_client.post(
            "/v1/ask/",
            headers=headers,
            json={
                "listingId": str(listing.id),
                "amount": 10000.00,
                "currency": "USD",
                "validUntil": future_date,
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["validUntil"] is not None

    @pytest.mark.asyncio
    async def test_create_ask_listing_not_open_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create ask on non-OPEN listing returns 403.

        Arrange: Create a WITHDRAWN listing.
        Act: POST /v1/ask with listing ID.
        Assert: Response is 403.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(
            db_session, seller_company
        )

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_withdrawn(
            db_session, instrument, seller_company, seller_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/ask/",
            headers=headers,
            json={
                "listingId": str(listing.id),
                "amount": 10000.00,
                "currency": "USD",
            },
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_ask_non_owner_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create ask by non-owner returns 403.

        Arrange: Create a listing owned by another company.
        Act: POST /v1/ask as non-owner.
        Assert: Response is 403.
        """
        # Arrange
        seller_company = await CompanyFactory.create(
            db_session, legal_name="Seller Co"
        )
        other_company = await CompanyFactory.create(
            db_session, legal_name="Other Co"
        )
        seller_user = await UserFactory.create_issuer(
            db_session, seller_company
        )
        other_user = await UserFactory.create_issuer(db_session, other_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(other_user.id),
            role=UserRole.ISSUER,
            company_id=str(other_company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/ask/",
            headers=headers,
            json={
                "listingId": str(listing.id),
                "amount": 10000.00,
                "currency": "USD",
            },
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_ask_invalid_amount_returns_422(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create ask with zero or negative amount returns 422.

        Arrange: Create a listing.
        Act: POST /v1/ask with amount <= 0.
        Assert: Response is 422.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(
            db_session, seller_company
        )

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/ask/",
            headers=headers,
            json={
                "listingId": str(listing.id),
                "amount": 0,
                "currency": "USD",
            },
        )

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_ask_past_valid_until_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create ask with valid_until in the past returns 403.

        Arrange: Create a listing.
        Act: POST /v1/ask with valid_until in the past.
        Assert: Response is 403.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(
            db_session, seller_company
        )

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        past_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

        # Act
        response = await test_client.post(
            "/v1/ask/",
            headers=headers,
            json={
                "listingId": str(listing.id),
                "amount": 10000.00,
                "currency": "USD",
                "validUntil": past_date,
            },
        )

        # Assert
        assert response.status_code == 403


class TestAskStatusTransition:
    """Tests for POST /v1/ask/{ask_id}/transition endpoint."""

    @pytest.mark.asyncio
    async def test_owner_withdraw_ask_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test owner can withdraw their ACTIVE ask.

        Arrange: Create an ACTIVE ask.
        Act: POST /v1/ask/{ask_id}/transition to WITHDRAWN.
        Assert: Response is 200 with WITHDRAWN status.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(
            db_session, seller_company
        )

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        ask = await AskFactory.create_active(
            db_session, listing, seller_company, seller_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/ask/{ask.id}/transition",
            headers=headers,
            json={"status": "WITHDRAWN"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "WITHDRAWN"

    @pytest.mark.asyncio
    async def test_admin_suspend_ask_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test admin can suspend an ACTIVE ask.

        Arrange: Create an ACTIVE ask.
        Act: POST /v1/ask/{ask_id}/transition to SUSPENDED as admin.
        Assert: Response is 200 with SUSPENDED status.
        """
        # Arrange
        seller_company = await CompanyFactory.create(
            db_session, legal_name="Seller Co"
        )
        admin_company = await CompanyFactory.create(
            db_session, legal_name="Admin Co"
        )
        seller_user = await UserFactory.create_issuer(
            db_session, seller_company
        )
        admin_user = await UserFactory.create_admin(db_session, admin_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        ask = await AskFactory.create_active(
            db_session, listing, seller_company, seller_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin_user.id),
            role=UserRole.ADMIN,
            company_id=str(admin_company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/ask/{ask.id}/transition",
            headers=headers,
            json={"status": "SUSPENDED"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUSPENDED"

    @pytest.mark.asyncio
    async def test_admin_reactivate_suspended_ask_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test admin can reactivate a SUSPENDED ask.

        Arrange: Create a SUSPENDED ask.
        Act: POST /v1/ask/{ask_id}/transition to ACTIVE as admin.
        Assert: Response is 200 with ACTIVE status.
        """
        # Arrange
        seller_company = await CompanyFactory.create(
            db_session, legal_name="Seller Co"
        )
        admin_company = await CompanyFactory.create(
            db_session, legal_name="Admin Co"
        )
        seller_user = await UserFactory.create_issuer(
            db_session, seller_company
        )
        admin_user = await UserFactory.create_admin(db_session, admin_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        ask = await AskFactory.create_suspended(
            db_session, listing, seller_company, seller_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin_user.id),
            role=UserRole.ADMIN,
            company_id=str(admin_company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/ask/{ask.id}/transition",
            headers=headers,
            json={"status": "ACTIVE"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_owner_cannot_reactivate_withdrawn_ask(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test owner cannot transition WITHDRAWN ask to ACTIVE.

        Arrange: Create a WITHDRAWN ask.
        Act: POST /v1/ask/{ask_id}/transition to ACTIVE as owner.
        Assert: Response is 403.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(
            db_session, seller_company
        )

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        ask = await AskFactory.create_withdrawn(
            db_session, listing, seller_company, seller_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/ask/{ask.id}/transition",
            headers=headers,
            json={"status": "ACTIVE"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_non_owner_cannot_withdraw_ask(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test non-owner cannot withdraw an ask.

        Arrange: Create an ask owned by another company.
        Act: POST /v1/ask/{ask_id}/transition to WITHDRAWN as non-owner.
        Assert: Response is 403.
        """
        # Arrange
        seller_company = await CompanyFactory.create(
            db_session, legal_name="Seller Co"
        )
        other_company = await CompanyFactory.create(
            db_session, legal_name="Other Co"
        )
        seller_user = await UserFactory.create_issuer(
            db_session, seller_company
        )
        other_user = await UserFactory.create_issuer(db_session, other_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        ask = await AskFactory.create_active(
            db_session, listing, seller_company, seller_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(other_user.id),
            role=UserRole.ISSUER,
            company_id=str(other_company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/ask/{ask.id}/transition",
            headers=headers,
            json={"status": "WITHDRAWN"},
        )

        # Assert
        assert response.status_code == 403


class TestUpdateAsk:
    """Tests for PATCH /v1/ask/{ask_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_ask_amount_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test owner can update ask amount.

        Arrange: Create an ACTIVE ask.
        Act: PATCH /v1/ask/{ask_id} with new amount.
        Assert: Response is 200 with updated amount.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(
            db_session, seller_company
        )

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        ask = await AskFactory.create_active(
            db_session, listing, seller_company, seller_user, amount=10000.00
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.patch(
            f"/v1/ask/{ask.id}",
            headers=headers,
            json={"amount": 12000.00},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 12000.00

    @pytest.mark.asyncio
    async def test_update_withdrawn_ask_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test cannot update WITHDRAWN ask.

        Arrange: Create a WITHDRAWN ask.
        Act: PATCH /v1/ask/{ask_id} with new amount.
        Assert: Response is 403.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(
            db_session, seller_company
        )

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        ask = await AskFactory.create_withdrawn(
            db_session, listing, seller_company, seller_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.patch(
            f"/v1/ask/{ask.id}",
            headers=headers,
            json={"amount": 12000.00},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_ask_non_owner_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test non-owner cannot update ask.

        Arrange: Create an ask owned by another company.
        Act: PATCH /v1/ask/{ask_id} as non-owner.
        Assert: Response is 403.
        """
        # Arrange
        seller_company = await CompanyFactory.create(
            db_session, legal_name="Seller Co"
        )
        other_company = await CompanyFactory.create(
            db_session, legal_name="Other Co"
        )
        seller_user = await UserFactory.create_issuer(
            db_session, seller_company
        )
        other_user = await UserFactory.create_issuer(db_session, other_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        ask = await AskFactory.create_active(
            db_session, listing, seller_company, seller_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(other_user.id),
            role=UserRole.ISSUER,
            company_id=str(other_company.id),
        )

        # Act
        response = await test_client.patch(
            f"/v1/ask/{ask.id}",
            headers=headers,
            json={"amount": 12000.00},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_ask_on_closed_listing_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test cannot update ask when listing is not OPEN.

        Arrange: Create an ask on a CLOSED listing.
        Act: PATCH /v1/ask/{ask_id} with new amount.
        Assert: Response is 403.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(
            db_session, seller_company
        )

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        # Create OPEN listing first, then update to CLOSED
        listing = await ListingFactory.create_closed(
            db_session, instrument, seller_company, seller_user
        )
        # Create ask directly with the listing (in a real scenario this would be created when listing was OPEN)
        ask = await AskFactory.create_active(
            db_session, listing, seller_company, seller_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.patch(
            f"/v1/ask/{ask.id}",
            headers=headers,
            json={"amount": 12000.00},
        )

        # Assert
        assert response.status_code == 403
