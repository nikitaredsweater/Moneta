"""
Integration tests for the Bid router (/v1/bid).

Tests bid CRUD operations with various scenarios:
- Search bids
- Get bid by ID
- Create bid
- Bid status transitions
- Accept bid
- Reject bid
"""

import pytest
from app.enums import BidStatus, ListingStatus, UserRole
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.factories import (
    BidFactory,
    CompanyFactory,
    InstrumentFactory,
    InstrumentOwnershipFactory,
    ListingFactory,
    UserFactory,
)


class TestSearchBids:
    """Tests for POST /v1/bid/search endpoint."""

    @pytest.mark.asyncio
    async def test_search_bids_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test search bids returns list of bids.

        Arrange: Create listings and bids.
        Act: POST /v1/bid/search with valid auth.
        Assert: Response is 200 with list of bids.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session, legal_name="Seller Co")
        bidder_company = await CompanyFactory.create(db_session, legal_name="Bidder Co")
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        await BidFactory.create_pending(
            db_session, listing, bidder_company, bidder_user, amount=10000.00
        )
        await BidFactory.create_pending(
            db_session, listing, bidder_company, bidder_user, amount=15000.00
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/bid/search",
            headers=headers,
            json={},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    @pytest.mark.asyncio
    async def test_search_bids_with_status_filter(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test search bids by status filter.

        Arrange: Create bids with different statuses.
        Act: POST /v1/bid/search with status filter.
        Assert: Response contains only bids with matching status.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        await BidFactory.create_pending(db_session, listing, bidder_company, bidder_user)
        await BidFactory.create_withdrawn(
            db_session, listing, bidder_company, bidder_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/bid/search",
            headers=headers,
            json={"status": "PENDING"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        statuses = [bid["status"] for bid in data]
        assert all(s == "PENDING" for s in statuses)

    @pytest.mark.asyncio
    async def test_search_bids_with_listing_filter(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test search bids by listing ID filter.

        Arrange: Create bids on different listings.
        Act: POST /v1/bid/search with listingId filter.
        Assert: Response contains only bids for matching listing.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

        instrument1 = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        instrument2 = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument1, seller_company
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument2, seller_company
        )
        listing1 = await ListingFactory.create_open(
            db_session, instrument1, seller_company, seller_user
        )
        listing2 = await ListingFactory.create_open(
            db_session, instrument2, seller_company, seller_user
        )
        await BidFactory.create_pending(
            db_session, listing1, bidder_company, bidder_user
        )
        await BidFactory.create_pending(
            db_session, listing2, bidder_company, bidder_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/bid/search",
            headers=headers,
            json={"listingId": [str(listing1.id)]},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        listing_ids = [bid["listingId"] for bid in data]
        assert all(lid == str(listing1.id) for lid in listing_ids)

    @pytest.mark.asyncio
    async def test_search_bids_with_listing_include(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test search bids with listing include.

        Arrange: Create bid on a listing.
        Act: POST /v1/bid/search with ?include=listing.
        Assert: Response contains bids with nested listing.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        await BidFactory.create_pending(db_session, listing, bidder_company, bidder_user)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/bid/search?include=listing",
            headers=headers,
            json={},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        bid_with_listing = next(
            (b for b in data if b["listingId"] == str(listing.id)), None
        )
        assert bid_with_listing is not None
        assert bid_with_listing["listing"] is not None
        assert bid_with_listing["listing"]["id"] == str(listing.id)

    @pytest.mark.asyncio
    async def test_search_bids_pagination(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test search bids with pagination.

        Arrange: Create multiple bids.
        Act: POST /v1/bid/search with limit and offset.
        Assert: Response contains paginated results.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        for i in range(5):
            await BidFactory.create_pending(
                db_session, listing, bidder_company, bidder_user, amount=10000.0 + i * 1000
            )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act - Get first 2 bids
        response = await test_client.post(
            "/v1/bid/search",
            headers=headers,
            json={"limit": 2, "offset": 0},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    @pytest.mark.skip(
        reason="All roles have VIEW.INSTRUMENT permission; no role exists to test 403"
    )
    async def test_search_bids_without_permission_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test search bids without VIEW.INSTRUMENT permission returns 403.

        Arrange: Create company and buyer user.
        Act: POST /v1/bid/search with buyer auth.
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
            "/v1/bid/search",
            headers=headers,
            json={},
        )

        # Assert
        assert response.status_code == 403


class TestGetBidById:
    """Tests for GET /v1/bid/{bid_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_bid_by_id_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get bid by ID returns bid data.

        Arrange: Create bid.
        Act: GET /v1/bid/{bid_id} with valid auth.
        Assert: Response is 200 with bid data.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        bid = await BidFactory.create_pending(
            db_session, listing, bidder_company, bidder_user, amount=12500.00
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.get(f"/v1/bid/{bid.id}", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(bid.id)
        assert data["listingId"] == str(listing.id)
        assert data["bidderCompanyId"] == str(bidder_company.id)
        assert data["bidderUserId"] == str(bidder_user.id)
        assert data["amount"] == 12500.00
        assert data["currency"] == "USD"
        assert data["status"] == "PENDING"

    @pytest.mark.asyncio
    async def test_get_bid_by_nonexistent_id_returns_404(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get bid by non-existent ID returns 404.

        Arrange: Create company and user for auth.
        Act: GET /v1/bid/{fake_uuid} with valid auth.
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
        response = await test_client.get(f"/v1/bid/{fake_uuid}", headers=headers)

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_bid_with_include_listing(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get bid with include=listing returns nested listing.

        Arrange: Create bid on a listing.
        Act: GET /v1/bid/{bid_id}?include=listing.
        Assert: Response contains bid with nested listing data.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        bid = await BidFactory.create_pending(
            db_session, listing, bidder_company, bidder_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.get(
            f"/v1/bid/{bid.id}?include=listing", headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["listing"] is not None
        assert data["listing"]["id"] == str(listing.id)

    @pytest.mark.asyncio
    async def test_get_bid_without_include_returns_null_listing(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get bid without include returns null listing.

        Arrange: Create bid.
        Act: GET /v1/bid/{bid_id} without include.
        Assert: Response contains bid with listing as null.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        bid = await BidFactory.create_pending(
            db_session, listing, bidder_company, bidder_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.get(f"/v1/bid/{bid.id}", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data.get("listing") is None


class TestCreateBid:
    """Tests for POST /v1/bid endpoint."""

    @pytest.mark.asyncio
    async def test_create_bid_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create bid with valid data returns created bid.

        Arrange: Create seller company with listing, bidder company with user.
        Act: POST /v1/bid with listing_id and amount.
        Assert: Response is 200 with created bid.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session, legal_name="Seller Co")
        bidder_company = await CompanyFactory.create(db_session, legal_name="Bidder Co")
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

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
            user_id=str(bidder_user.id),
            role=UserRole.ISSUER,
            company_id=str(bidder_company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/bid/",
            headers=headers,
            json={
                "listingId": str(listing.id),
                "amount": 20000.00,
                "currency": "USD",
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["listingId"] == str(listing.id)
        assert data["bidderCompanyId"] == str(bidder_company.id)
        assert data["bidderUserId"] == str(bidder_user.id)
        assert data["amount"] == 20000.00
        assert data["currency"] == "USD"
        assert data["status"] == "PENDING"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_bid_with_valid_until(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create bid with validUntil timestamp.

        Arrange: Create listing and bidder user.
        Act: POST /v1/bid with validUntil.
        Assert: Response is 200 with validUntil set.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

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
            user_id=str(bidder_user.id),
            role=UserRole.ISSUER,
            company_id=str(bidder_company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/bid/",
            headers=headers,
            json={
                "listingId": str(listing.id),
                "amount": 25000.00,
                "currency": "EUR",
                "validUntil": "2025-12-31T23:59:59Z",
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["validUntil"] is not None

    @pytest.mark.asyncio
    async def test_create_bid_nonexistent_listing_returns_404(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create bid with non-existent listing returns 404.

        Arrange: Create company and user.
        Act: POST /v1/bid with fake listing_id.
        Assert: Response is 404 Not Found.
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
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        # Act
        response = await test_client.post(
            "/v1/bid/",
            headers=headers,
            json={
                "listingId": fake_uuid,
                "amount": 10000.00,
                "currency": "USD",
            },
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Listing" in data["detail"]

    @pytest.mark.asyncio
    async def test_create_bid_on_non_open_listing_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create bid on non-OPEN listing returns 403.

        Arrange: Create WITHDRAWN listing and bidder user.
        Act: POST /v1/bid.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

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
            user_id=str(bidder_user.id),
            role=UserRole.ISSUER,
            company_id=str(bidder_company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/bid/",
            headers=headers,
            json={
                "listingId": str(listing.id),
                "amount": 10000.00,
                "currency": "USD",
            },
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "not open" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_bid_on_own_listing_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create bid on own listing returns 403 (no self-bidding).

        Arrange: Create listing and try to bid as seller.
        Act: POST /v1/bid with same company as seller.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)

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
            "/v1/bid/",
            headers=headers,
            json={
                "listingId": str(listing.id),
                "amount": 10000.00,
                "currency": "USD",
            },
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "own listing" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_multiple_bids_same_company_succeeds(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test one company can make multiple bids on the same listing.

        Arrange: Create listing and bidder company.
        Act: POST /v1/bid twice with same company.
        Assert: Both responses are 200 with different bids.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

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
            user_id=str(bidder_user.id),
            role=UserRole.ISSUER,
            company_id=str(bidder_company.id),
        )

        # Act - First bid
        response1 = await test_client.post(
            "/v1/bid/",
            headers=headers,
            json={
                "listingId": str(listing.id),
                "amount": 10000.00,
                "currency": "USD",
            },
        )

        # Act - Second bid
        response2 = await test_client.post(
            "/v1/bid/",
            headers=headers,
            json={
                "listingId": str(listing.id),
                "amount": 15000.00,
                "currency": "USD",
            },
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        data1 = response1.json()
        data2 = response2.json()
        assert data1["id"] != data2["id"]
        assert data1["amount"] == 10000.00
        assert data2["amount"] == 15000.00

    @pytest.mark.asyncio
    async def test_create_bid_without_permission_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create bid without UPDATE.INSTRUMENT permission returns 403.

        Arrange: Create listing and buyer user.
        Act: POST /v1/bid with buyer auth.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_buyer = await UserFactory.create(
            db_session, bidder_company, role=UserRole.BUYER
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
            user_id=str(bidder_buyer.id),
            role=UserRole.BUYER,
            company_id=str(bidder_company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/bid/",
            headers=headers,
            json={
                "listingId": str(listing.id),
                "amount": 10000.00,
                "currency": "USD",
            },
        )

        # Assert
        assert response.status_code == 403


class TestBidStatusTransition:
    """Tests for POST /v1/bid/{bid_id}/transition endpoint."""

    @pytest.mark.asyncio
    async def test_transition_pending_to_withdrawn_by_bidder_company(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test bidder company can transition PENDING to WITHDRAWN.

        Arrange: Create PENDING bid.
        Act: POST /v1/bid/{id}/transition with WITHDRAWN status by bidder.
        Assert: Status is changed to WITHDRAWN.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        bid = await BidFactory.create_pending(
            db_session, listing, bidder_company, bidder_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(bidder_user.id),
            role=UserRole.ISSUER,
            company_id=str(bidder_company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/bid/{bid.id}/transition",
            headers=headers,
            json={"status": "WITHDRAWN"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "WITHDRAWN"

    @pytest.mark.asyncio
    async def test_transition_pending_to_suspended_by_admin(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test admin can transition PENDING to SUSPENDED.

        Arrange: Create PENDING bid.
        Act: POST /v1/bid/{id}/transition with SUSPENDED status by admin.
        Assert: Status is changed to SUSPENDED.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, seller_company)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        bid = await BidFactory.create_pending(
            db_session, listing, bidder_company, bidder_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/bid/{bid.id}/transition",
            headers=headers,
            json={"status": "SUSPENDED"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUSPENDED"

    @pytest.mark.asyncio
    async def test_transition_withdrawn_to_suspended_by_admin(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test admin can transition WITHDRAWN to SUSPENDED.

        Arrange: Create WITHDRAWN bid.
        Act: POST /v1/bid/{id}/transition with SUSPENDED status by admin.
        Assert: Status is changed to SUSPENDED.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, seller_company)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        bid = await BidFactory.create_withdrawn(
            db_session, listing, bidder_company, bidder_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/bid/{bid.id}/transition",
            headers=headers,
            json={"status": "SUSPENDED"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUSPENDED"

    @pytest.mark.asyncio
    async def test_transition_pending_to_suspended_by_company_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test company user cannot transition PENDING to SUSPENDED.

        Arrange: Create PENDING bid.
        Act: POST /v1/bid/{id}/transition with SUSPENDED status by company user.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        bid = await BidFactory.create_pending(
            db_session, listing, bidder_company, bidder_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(bidder_user.id),
            role=UserRole.ISSUER,
            company_id=str(bidder_company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/bid/{bid.id}/transition",
            headers=headers,
            json={"status": "SUSPENDED"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_transition_by_non_bidder_company_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test user from different company cannot transition bid.

        Arrange: Create bid, user from third company.
        Act: POST /v1/bid/{id}/transition by non-bidder company.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        other_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)
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
        bid = await BidFactory.create_pending(
            db_session, listing, bidder_company, bidder_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(other_user.id),
            role=UserRole.ISSUER,
            company_id=str(other_company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/bid/{bid.id}/transition",
            headers=headers,
            json={"status": "WITHDRAWN"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_transition_on_non_open_listing_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test transition fails when listing is not OPEN.

        Arrange: Create bid on WITHDRAWN listing.
        Act: POST /v1/bid/{id}/transition.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        # Create as OPEN first, then we'll change it
        listing = await ListingFactory.create(
            db_session, instrument, seller_company, seller_user, status=ListingStatus.OPEN
        )
        bid = await BidFactory.create_pending(
            db_session, listing, bidder_company, bidder_user
        )
        # Now change the listing to WITHDRAWN
        listing.status = ListingStatus.WITHDRAWN
        await db_session.commit()

        headers = auth_headers(
            user_id=str(bidder_user.id),
            role=UserRole.ISSUER,
            company_id=str(bidder_company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/bid/{bid.id}/transition",
            headers=headers,
            json={"status": "WITHDRAWN"},
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "not open" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_transition_nonexistent_bid_returns_404(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test transition on non-existent bid returns 404.

        Arrange: Create company and user for auth.
        Act: POST /v1/bid/{fake_id}/transition.
        Assert: Response is 404 Not Found.
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
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        # Act
        response = await test_client.post(
            f"/v1/bid/{fake_uuid}/transition",
            headers=headers,
            json={"status": "WITHDRAWN"},
        )

        # Assert
        assert response.status_code == 404


class TestAcceptBid:
    """Tests for POST /v1/bid/{bid_id}/accept endpoint."""

    @pytest.mark.asyncio
    async def test_accept_bid_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test accept bid sets status to SELECTED.

        Arrange: Create PENDING bid.
        Act: POST /v1/bid/{id}/accept by seller company.
        Assert: Bid status is SELECTED.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        bid = await BidFactory.create_pending(
            db_session, listing, bidder_company, bidder_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/bid/{bid.id}/accept",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SELECTED"

    @pytest.mark.asyncio
    async def test_accept_bid_rejects_other_pending_bids(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test accepting a bid sets other PENDING bids to NOT_SELECTED.

        Arrange: Create multiple PENDING bids.
        Act: POST /v1/bid/{id}/accept on one bid.
        Assert: Other bids are set to NOT_SELECTED.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company1 = await CompanyFactory.create(db_session)
        bidder_company2 = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user1 = await UserFactory.create_issuer(db_session, bidder_company1)
        bidder_user2 = await UserFactory.create_issuer(db_session, bidder_company2)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        bid1 = await BidFactory.create_pending(
            db_session, listing, bidder_company1, bidder_user1, amount=10000.00
        )
        bid2 = await BidFactory.create_pending(
            db_session, listing, bidder_company2, bidder_user2, amount=15000.00
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act - Accept bid1
        response = await test_client.post(
            f"/v1/bid/{bid1.id}/accept",
            headers=headers,
        )

        # Assert - bid1 is SELECTED
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SELECTED"

        # Check bid2 is NOT_SELECTED
        response2 = await test_client.get(f"/v1/bid/{bid2.id}", headers=headers)
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["status"] == "NOT_SELECTED"

    @pytest.mark.asyncio
    async def test_accept_bid_by_non_seller_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test accept bid by non-seller company returns 403.

        Arrange: Create bid, attempt accept by bidder company.
        Act: POST /v1/bid/{id}/accept by bidder company.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        bid = await BidFactory.create_pending(
            db_session, listing, bidder_company, bidder_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(bidder_user.id),
            role=UserRole.ISSUER,
            company_id=str(bidder_company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/bid/{bid.id}/accept",
            headers=headers,
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "listing owner" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_accept_non_pending_bid_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test accept non-PENDING bid returns 403.

        Arrange: Create WITHDRAWN bid.
        Act: POST /v1/bid/{id}/accept.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        bid = await BidFactory.create_withdrawn(
            db_session, listing, bidder_company, bidder_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/bid/{bid.id}/accept",
            headers=headers,
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "PENDING" in data["detail"]

    @pytest.mark.asyncio
    async def test_accept_bid_on_non_open_listing_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test accept bid fails when listing is not OPEN.

        Arrange: Create bid on WITHDRAWN listing.
        Act: POST /v1/bid/{id}/accept.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create(
            db_session, instrument, seller_company, seller_user, status=ListingStatus.OPEN
        )
        bid = await BidFactory.create_pending(
            db_session, listing, bidder_company, bidder_user
        )
        listing.status = ListingStatus.WITHDRAWN
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/bid/{bid.id}/accept",
            headers=headers,
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "not open" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_accept_nonexistent_bid_returns_404(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test accept non-existent bid returns 404.

        Arrange: Create company and user for auth.
        Act: POST /v1/bid/{fake_id}/accept.
        Assert: Response is 404 Not Found.
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
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        # Act
        response = await test_client.post(
            f"/v1/bid/{fake_uuid}/accept",
            headers=headers,
        )

        # Assert
        assert response.status_code == 404


class TestRejectBid:
    """Tests for POST /v1/bid/{bid_id}/reject endpoint."""

    @pytest.mark.asyncio
    async def test_reject_bid_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test reject bid sets status to NOT_SELECTED.

        Arrange: Create PENDING bid.
        Act: POST /v1/bid/{id}/reject by seller company.
        Assert: Bid status is NOT_SELECTED.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        bid = await BidFactory.create_pending(
            db_session, listing, bidder_company, bidder_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/bid/{bid.id}/reject",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "NOT_SELECTED"

    @pytest.mark.asyncio
    async def test_reject_bid_does_not_affect_other_bids(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test rejecting a bid does not affect other pending bids.

        Arrange: Create multiple PENDING bids.
        Act: POST /v1/bid/{id}/reject on one bid.
        Assert: Other bids remain PENDING.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company1 = await CompanyFactory.create(db_session)
        bidder_company2 = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user1 = await UserFactory.create_issuer(db_session, bidder_company1)
        bidder_user2 = await UserFactory.create_issuer(db_session, bidder_company2)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        bid1 = await BidFactory.create_pending(
            db_session, listing, bidder_company1, bidder_user1, amount=10000.00
        )
        bid2 = await BidFactory.create_pending(
            db_session, listing, bidder_company2, bidder_user2, amount=15000.00
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act - Reject bid1
        response = await test_client.post(
            f"/v1/bid/{bid1.id}/reject",
            headers=headers,
        )

        # Assert - bid1 is NOT_SELECTED
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "NOT_SELECTED"

        # Check bid2 is still PENDING
        response2 = await test_client.get(f"/v1/bid/{bid2.id}", headers=headers)
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["status"] == "PENDING"

    @pytest.mark.asyncio
    async def test_reject_bid_by_non_seller_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test reject bid by non-seller company returns 403.

        Arrange: Create bid, attempt reject by bidder company.
        Act: POST /v1/bid/{id}/reject by bidder company.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        bid = await BidFactory.create_pending(
            db_session, listing, bidder_company, bidder_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(bidder_user.id),
            role=UserRole.ISSUER,
            company_id=str(bidder_company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/bid/{bid.id}/reject",
            headers=headers,
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "listing owner" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_reject_non_pending_bid_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test reject non-PENDING bid returns 403.

        Arrange: Create SELECTED bid.
        Act: POST /v1/bid/{id}/reject.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create_open(
            db_session, instrument, seller_company, seller_user
        )
        bid = await BidFactory.create_selected(
            db_session, listing, bidder_company, bidder_user
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/bid/{bid.id}/reject",
            headers=headers,
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "PENDING" in data["detail"]

    @pytest.mark.asyncio
    async def test_reject_bid_on_non_open_listing_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test reject bid fails when listing is not OPEN.

        Arrange: Create bid on SUSPENDED listing.
        Act: POST /v1/bid/{id}/reject.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        seller_company = await CompanyFactory.create(db_session)
        bidder_company = await CompanyFactory.create(db_session)
        seller_user = await UserFactory.create_issuer(db_session, seller_company)
        bidder_user = await UserFactory.create_issuer(db_session, bidder_company)

        instrument = await InstrumentFactory.create_active(
            db_session, seller_company, seller_user
        )
        await InstrumentOwnershipFactory.create_active(
            db_session, instrument, seller_company
        )
        listing = await ListingFactory.create(
            db_session, instrument, seller_company, seller_user, status=ListingStatus.OPEN
        )
        bid = await BidFactory.create_pending(
            db_session, listing, bidder_company, bidder_user
        )
        listing.status = ListingStatus.SUSPENDED
        await db_session.commit()

        headers = auth_headers(
            user_id=str(seller_user.id),
            role=UserRole.ISSUER,
            company_id=str(seller_company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/bid/{bid.id}/reject",
            headers=headers,
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "not open" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_reject_nonexistent_bid_returns_404(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test reject non-existent bid returns 404.

        Arrange: Create company and user for auth.
        Act: POST /v1/bid/{fake_id}/reject.
        Assert: Response is 404 Not Found.
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
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        # Act
        response = await test_client.post(
            f"/v1/bid/{fake_uuid}/reject",
            headers=headers,
        )

        # Assert
        assert response.status_code == 404
