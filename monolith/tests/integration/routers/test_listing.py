"""
Integration tests for the Listing router (/v1/listing).

Tests listing CRUD operations with various scenarios:
- Search listings
- Get listing by ID
- Create listing
- Listing status transitions
"""

import pytest
from app.enums import ListingStatus, UserRole
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.factories import (
    CompanyFactory,
    InstrumentFactory,
    InstrumentOwnershipFactory,
    ListingFactory,
    UserFactory,
)


class TestSearchListings:
    """Tests for POST /v1/listing/search endpoint."""

    @pytest.mark.asyncio
    async def test_search_listings_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test search listings returns list of listings.

        Arrange: Create company, user, instrument, ownership, and listings.
        Act: POST /v1/listing/search with valid auth.
        Assert: Response is 200 with list of listings.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument1 = await InstrumentFactory.create_active(
            db_session, company, issuer, name="Instrument One"
        )
        instrument2 = await InstrumentFactory.create_active(
            db_session, company, issuer, name="Instrument Two"
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument1, company
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument2, company
        )
        await ListingFactory.create_open(
            db_session, instrument1, company, issuer
        )
        await ListingFactory.create_open(
            db_session, instrument2, company, issuer
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/listing/search",
            headers=headers,
            json={},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    @pytest.mark.asyncio
    async def test_search_listings_with_status_filter(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test search listings by status filter.

        Arrange: Create listings with different statuses.
        Act: POST /v1/listing/search with status filter.
        Assert: Response contains only listings with matching status.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument1 = await InstrumentFactory.create_active(db_session, company, issuer)
        instrument2 = await InstrumentFactory.create_active(db_session, company, issuer)
        await InstrumentOwnershipFactory.create_active(db_session, instrument1, company)
        await InstrumentOwnershipFactory.create_active(db_session, instrument2, company)
        await ListingFactory.create_open(db_session, instrument1, company, issuer)
        await ListingFactory.create_withdrawn(db_session, instrument2, company, issuer)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/listing/search",
            headers=headers,
            json={"status": "OPEN"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        statuses = [listing["status"] for listing in data]
        assert all(s == "OPEN" for s in statuses)

    @pytest.mark.asyncio
    async def test_search_listings_with_seller_company_filter(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test search listings by seller company filter.

        Arrange: Create listings from different companies.
        Act: POST /v1/listing/search with sellerCompanyId filter.
        Assert: Response contains only listings from matching company.
        """
        # Arrange
        company1 = await CompanyFactory.create(db_session, legal_name="Company One")
        company2 = await CompanyFactory.create(db_session, legal_name="Company Two")
        issuer1 = await UserFactory.create_issuer(db_session, company1)
        issuer2 = await UserFactory.create_issuer(db_session, company2)
        instrument1 = await InstrumentFactory.create_active(
            db_session, company1, issuer1
        )
        instrument2 = await InstrumentFactory.create_active(
            db_session, company2, issuer2
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument1, company1
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument2, company2
        )
        await ListingFactory.create_open(db_session, instrument1, company1, issuer1)
        await ListingFactory.create_open(db_session, instrument2, company2, issuer2)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer1.id),
            role=UserRole.ISSUER,
            company_id=str(company1.id),
        )

        # Act
        response = await test_client.post(
            "/v1/listing/search",
            headers=headers,
            json={"sellerCompanyId": [str(company1.id)]},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        seller_ids = [listing["sellerCompanyId"] for listing in data]
        assert all(s == str(company1.id) for s in seller_ids)

    @pytest.mark.asyncio
    async def test_search_listings_with_instrument_include(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test search listings with instrument include.

        Arrange: Create listing with instrument.
        Act: POST /v1/listing/search with ?include=instrument.
        Assert: Response contains listings with nested instrument.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create_active(
            db_session, company, issuer, name="Included Instrument"
        )
        await InstrumentOwnershipFactory.create_active(db_session, instrument, company)
        await ListingFactory.create_open(db_session, instrument, company, issuer)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/listing/search?include=instrument",
            headers=headers,
            json={},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        listing_with_instrument = next(
            (l for l in data if l["instrumentId"] == str(instrument.id)), None
        )
        assert listing_with_instrument is not None
        assert listing_with_instrument["instrument"] is not None
        assert listing_with_instrument["instrument"]["name"] == "Included Instrument"

    @pytest.mark.asyncio
    async def test_search_listings_without_include_returns_null_instrument(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test search listings without include returns null instrument.

        Arrange: Create listing with instrument.
        Act: POST /v1/listing/search without include.
        Assert: Response contains listings with instrument as null.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create_active(db_session, company, issuer)
        await InstrumentOwnershipFactory.create_active(db_session, instrument, company)
        await ListingFactory.create_open(db_session, instrument, company, issuer)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/listing/search",
            headers=headers,
            json={},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        listing = next(
            (l for l in data if l["instrumentId"] == str(instrument.id)), None
        )
        assert listing is not None
        assert listing.get("instrument") is None

    @pytest.mark.asyncio
    async def test_search_listings_pagination(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test search listings with pagination.

        Arrange: Create multiple listings.
        Act: POST /v1/listing/search with limit and offset.
        Assert: Response contains paginated results.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        for i in range(5):
            instrument = await InstrumentFactory.create_active(
                db_session, company, issuer, name=f"Instrument {i}"
            )
            await InstrumentOwnershipFactory.create_active(
                db_session, instrument, company
            )
            await ListingFactory.create_open(db_session, instrument, company, issuer)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act - Get first 2 listings
        response = await test_client.post(
            "/v1/listing/search",
            headers=headers,
            json={"limit": 2, "offset": 0},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_search_listings_without_permission_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test search listings without VIEW.INSTRUMENT permission returns 403.

        Arrange: Create company and buyer user.
        Act: POST /v1/listing/search with buyer auth.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        buyer = await UserFactory.create(db_session, company, role=UserRole.BUYER)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(buyer.id),
            role=UserRole.BUYER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/listing/search",
            headers=headers,
            json={},
        )

        # Assert - BUYER should not have VIEW.INSTRUMENT permission
        assert response.status_code == 403


class TestGetListingById:
    """Tests for GET /v1/listing/{listing_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_listing_by_id_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get listing by ID returns listing data.

        Arrange: Create company, user, instrument, ownership, and listing.
        Act: GET /v1/listing/{listing_id} with valid auth.
        Assert: Response is 200 with listing data.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create_active(db_session, company, issuer)
        await InstrumentOwnershipFactory.create_active(db_session, instrument, company)
        listing = await ListingFactory.create_open(
            db_session, instrument, company, issuer
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.get(
            f"/v1/listing/{listing.id}", headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(listing.id)
        assert data["instrumentId"] == str(instrument.id)
        assert data["sellerCompanyId"] == str(company.id)
        assert data["status"] == "OPEN"

    @pytest.mark.asyncio
    async def test_get_listing_by_nonexistent_id_returns_404(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get listing by non-existent ID returns 404.

        Arrange: Create company and user for auth.
        Act: GET /v1/listing/{fake_uuid} with valid auth.
        Assert: Response is 404 Not Found.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        # Act
        response = await test_client.get(
            f"/v1/listing/{fake_uuid}", headers=headers
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_listing_with_include_instrument(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get listing with include=instrument returns nested instrument.

        Arrange: Create listing with instrument.
        Act: GET /v1/listing/{listing_id}?include=instrument.
        Assert: Response contains listing with nested instrument data.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create_active(
            db_session, company, issuer, name="Nested Instrument"
        )
        await InstrumentOwnershipFactory.create_active(db_session, instrument, company)
        listing = await ListingFactory.create_open(
            db_session, instrument, company, issuer
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.get(
            f"/v1/listing/{listing.id}?include=instrument", headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["instrument"] is not None
        assert data["instrument"]["name"] == "Nested Instrument"
        assert data["instrument"]["id"] == str(instrument.id)

    @pytest.mark.asyncio
    async def test_get_listing_without_include_returns_null_instrument(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get listing without include returns null instrument.

        Arrange: Create listing with instrument.
        Act: GET /v1/listing/{listing_id} without include.
        Assert: Response contains listing with instrument as null.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create_active(db_session, company, issuer)
        await InstrumentOwnershipFactory.create_active(db_session, instrument, company)
        listing = await ListingFactory.create_open(
            db_session, instrument, company, issuer
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.get(
            f"/v1/listing/{listing.id}", headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data.get("instrument") is None


class TestCreateListing:
    """Tests for POST /v1/listing endpoint."""

    @pytest.mark.asyncio
    async def test_create_listing_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create listing with valid data returns created listing.

        Arrange: Create company, user, instrument, and active ownership.
        Act: POST /v1/listing with instrument_id.
        Assert: Response is 200 with created listing.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create_active(db_session, company, issuer)
        await InstrumentOwnershipFactory.create_active(db_session, instrument, company)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/listing/",
            headers=headers,
            json={"instrumentId": str(instrument.id)},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["instrumentId"] == str(instrument.id)
        assert data["sellerCompanyId"] == str(company.id)
        assert data["listingCreatorUserId"] == str(issuer.id)
        assert data["status"] == "OPEN"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_listing_nonexistent_instrument_returns_404(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create listing with non-existent instrument returns 404.

        Arrange: Create company and user.
        Act: POST /v1/listing with fake instrument_id.
        Assert: Response is 404 Not Found.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        # Act
        response = await test_client.post(
            "/v1/listing/",
            headers=headers,
            json={"instrumentId": fake_uuid},
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Instrument" in data["detail"]

    @pytest.mark.asyncio
    async def test_create_listing_company_not_owner_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create listing when company doesn't own instrument returns 403.

        Arrange: Create two companies, instrument owned by company1, user from company2.
        Act: POST /v1/listing with user from company2.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        company1 = await CompanyFactory.create(db_session, legal_name="Owner Company")
        company2 = await CompanyFactory.create(db_session, legal_name="Other Company")
        issuer1 = await UserFactory.create_issuer(db_session, company1)
        issuer2 = await UserFactory.create_issuer(db_session, company2)
        instrument = await InstrumentFactory.create_active(
            db_session, company1, issuer1
        )
        await InstrumentOwnershipFactory.create_active(db_session, instrument, company1)
        await db_session.commit()

        # User from company2 trying to create listing
        headers = auth_headers(
            user_id=str(issuer2.id),
            role=UserRole.ISSUER,
            company_id=str(company2.id),
        )

        # Act
        response = await test_client.post(
            "/v1/listing/",
            headers=headers,
            json={"instrumentId": str(instrument.id)},
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "does not own" in data["detail"]

    @pytest.mark.asyncio
    async def test_create_listing_no_active_ownership_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create listing when instrument has no active owner returns 403.

        Arrange: Create instrument without any active ownership.
        Act: POST /v1/listing.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create_active(db_session, company, issuer)
        # Note: No ownership created
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/listing/",
            headers=headers,
            json={"instrumentId": str(instrument.id)},
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "no active owner" in data["detail"]

    @pytest.mark.asyncio
    async def test_create_listing_open_listing_exists_returns_409(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create listing when OPEN listing already exists returns 409.

        Arrange: Create instrument with existing OPEN listing.
        Act: POST /v1/listing.
        Assert: Response is 409 Conflict.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create_active(db_session, company, issuer)
        await InstrumentOwnershipFactory.create_active(db_session, instrument, company)
        await ListingFactory.create_open(db_session, instrument, company, issuer)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/listing/",
            headers=headers,
            json={"instrumentId": str(instrument.id)},
        )

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert "already exists" in data["detail"]

    @pytest.mark.asyncio
    async def test_create_listing_after_withdrawn_succeeds(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create listing after previous listing was withdrawn succeeds.

        Arrange: Create instrument with WITHDRAWN listing.
        Act: POST /v1/listing.
        Assert: Response is 200 with new OPEN listing.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create_active(db_session, company, issuer)
        await InstrumentOwnershipFactory.create_active(db_session, instrument, company)
        await ListingFactory.create_withdrawn(db_session, instrument, company, issuer)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/listing/",
            headers=headers,
            json={"instrumentId": str(instrument.id)},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OPEN"

    @pytest.mark.asyncio
    async def test_create_listing_without_permission_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create listing without UPDATE.INSTRUMENT permission returns 403.

        Arrange: Create company and buyer user.
        Act: POST /v1/listing with buyer auth.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        buyer = await UserFactory.create(db_session, company, role=UserRole.BUYER)
        instrument = await InstrumentFactory.create_active(
            db_session, company, buyer
        )
        await InstrumentOwnershipFactory.create_active(db_session, instrument, company)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(buyer.id),
            role=UserRole.BUYER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/listing/",
            headers=headers,
            json={"instrumentId": str(instrument.id)},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_listing_by_admin_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test admin can create listing.

        Arrange: Create company, admin, instrument with ownership.
        Act: POST /v1/listing with admin auth.
        Assert: Response is 200 with created listing.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, company)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create_active(
            db_session, company, issuer
        )
        await InstrumentOwnershipFactory.create_active(db_session, instrument, company)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/listing/",
            headers=headers,
            json={"instrumentId": str(instrument.id)},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OPEN"


class TestListingStatusTransition:
    """Tests for POST /v1/listing/{listing_id}/transition endpoint."""

    @pytest.mark.asyncio
    async def test_transition_open_to_withdrawn_by_company_user(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test company user can transition OPEN to WITHDRAWN.

        Arrange: Create OPEN listing.
        Act: POST /v1/listing/{id}/transition with WITHDRAWN status.
        Assert: Status is changed to WITHDRAWN.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create_active(db_session, company, issuer)
        await InstrumentOwnershipFactory.create_active(db_session, instrument, company)
        listing = await ListingFactory.create_open(
            db_session, instrument, company, issuer
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/listing/{listing.id}/transition",
            headers=headers,
            json={"status": "WITHDRAWN"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "WITHDRAWN"

    @pytest.mark.asyncio
    async def test_transition_open_to_suspended_by_company_user_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test company user cannot transition OPEN to SUSPENDED.

        Arrange: Create OPEN listing.
        Act: POST /v1/listing/{id}/transition with SUSPENDED status.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create_active(db_session, company, issuer)
        await InstrumentOwnershipFactory.create_active(db_session, instrument, company)
        listing = await ListingFactory.create_open(
            db_session, instrument, company, issuer
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/listing/{listing.id}/transition",
            headers=headers,
            json={"status": "SUSPENDED"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_transition_open_to_suspended_by_admin(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test admin can transition OPEN to SUSPENDED.

        Arrange: Create OPEN listing.
        Act: POST /v1/listing/{id}/transition with SUSPENDED status by admin.
        Assert: Status is changed to SUSPENDED.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, company)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create_active(db_session, company, issuer)
        await InstrumentOwnershipFactory.create_active(db_session, instrument, company)
        listing = await ListingFactory.create_open(
            db_session, instrument, company, issuer
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/listing/{listing.id}/transition",
            headers=headers,
            json={"status": "SUSPENDED"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUSPENDED"

    @pytest.mark.asyncio
    async def test_admin_cannot_transition_open_to_withdrawn(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test admin cannot transition OPEN to WITHDRAWN.

        Arrange: Create OPEN listing.
        Act: POST /v1/listing/{id}/transition with WITHDRAWN status by admin.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, company)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create_active(db_session, company, issuer)
        await InstrumentOwnershipFactory.create_active(db_session, instrument, company)
        listing = await ListingFactory.create_open(
            db_session, instrument, company, issuer
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/listing/{listing.id}/transition",
            headers=headers,
            json={"status": "WITHDRAWN"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_cannot_transition_withdrawn_to_open(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test admin cannot transition WITHDRAWN to OPEN.

        Arrange: Create WITHDRAWN listing.
        Act: POST /v1/listing/{id}/transition with OPEN status by admin.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, company)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create_active(db_session, company, issuer)
        await InstrumentOwnershipFactory.create_active(db_session, instrument, company)
        listing = await ListingFactory.create_withdrawn(
            db_session, instrument, company, issuer
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/listing/{listing.id}/transition",
            headers=headers,
            json={"status": "OPEN"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_transition_suspended_to_open(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test admin can transition SUSPENDED to OPEN.

        Arrange: Create SUSPENDED listing.
        Act: POST /v1/listing/{id}/transition with OPEN status by admin.
        Assert: Status is changed to OPEN.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, company)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create_active(db_session, company, issuer)
        await InstrumentOwnershipFactory.create_active(db_session, instrument, company)
        listing = await ListingFactory.create_suspended(
            db_session, instrument, company, issuer
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/listing/{listing.id}/transition",
            headers=headers,
            json={"status": "OPEN"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OPEN"

    @pytest.mark.asyncio
    async def test_admin_can_transition_open_to_closed(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test admin can transition OPEN to CLOSED.

        Arrange: Create OPEN listing.
        Act: POST /v1/listing/{id}/transition with CLOSED status by admin.
        Assert: Status is changed to CLOSED.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, company)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create_active(db_session, company, issuer)
        await InstrumentOwnershipFactory.create_active(db_session, instrument, company)
        listing = await ListingFactory.create_open(
            db_session, instrument, company, issuer
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/listing/{listing.id}/transition",
            headers=headers,
            json={"status": "CLOSED"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CLOSED"

    @pytest.mark.asyncio
    async def test_transition_nonexistent_listing_returns_404(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test transition on non-existent listing returns 404.

        Arrange: Create company and user for auth.
        Act: POST /v1/listing/{fake_id}/transition.
        Assert: Response is 404 Not Found.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        # Act
        response = await test_client.post(
            f"/v1/listing/{fake_uuid}/transition",
            headers=headers,
            json={"status": "WITHDRAWN"},
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_transition_by_other_company_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test transition by user from different company returns 403.

        Arrange: Create listing owned by company1, user from company2.
        Act: POST /v1/listing/{id}/transition with company2 user.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        company1 = await CompanyFactory.create(db_session, legal_name="Seller Company")
        company2 = await CompanyFactory.create(db_session, legal_name="Other Company")
        issuer1 = await UserFactory.create_issuer(db_session, company1)
        issuer2 = await UserFactory.create_issuer(db_session, company2)
        instrument = await InstrumentFactory.create_active(
            db_session, company1, issuer1
        )
        await InstrumentOwnershipFactory.create_active(db_session, instrument, company1)
        listing = await ListingFactory.create_open(
            db_session, instrument, company1, issuer1
        )
        await db_session.commit()

        # User from company2 trying to transition
        headers = auth_headers(
            user_id=str(issuer2.id),
            role=UserRole.ISSUER,
            company_id=str(company2.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/listing/{listing.id}/transition",
            headers=headers,
            json={"status": "WITHDRAWN"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_transition_same_status_returns_listing(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test transition to same status returns listing unchanged.

        Arrange: Create OPEN listing.
        Act: POST /v1/listing/{id}/transition with OPEN status.
        Assert: Response is 200 with unchanged listing.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create_active(db_session, company, issuer)
        await InstrumentOwnershipFactory.create_active(db_session, instrument, company)
        listing = await ListingFactory.create_open(
            db_session, instrument, company, issuer
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/listing/{listing.id}/transition",
            headers=headers,
            json={"status": "OPEN"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OPEN"

    @pytest.mark.asyncio
    async def test_transition_invalid_status_value_returns_422(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test transition with invalid status value returns 422.

        Arrange: Create listing.
        Act: POST /v1/listing/{id}/transition with invalid status.
        Assert: Response is 422 Unprocessable Entity.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create_active(db_session, company, issuer)
        await InstrumentOwnershipFactory.create_active(db_session, instrument, company)
        listing = await ListingFactory.create_open(
            db_session, instrument, company, issuer
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act - invalid status value
        response = await test_client.post(
            f"/v1/listing/{listing.id}/transition",
            headers=headers,
            json={"status": "INVALID_STATUS"},
        )

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_transition_without_permission_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test transition without UPDATE.INSTRUMENT permission returns 403.

        Arrange: Create listing and buyer user.
        Act: POST /v1/listing/{id}/transition with buyer auth.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        buyer = await UserFactory.create(db_session, company, role=UserRole.BUYER)
        instrument = await InstrumentFactory.create_active(db_session, company, issuer)
        await InstrumentOwnershipFactory.create_active(db_session, instrument, company)
        listing = await ListingFactory.create_open(
            db_session, instrument, company, issuer
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(buyer.id),
            role=UserRole.BUYER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/listing/{listing.id}/transition",
            headers=headers,
            json={"status": "WITHDRAWN"},
        )

        # Assert
        assert response.status_code == 403
