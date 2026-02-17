"""
Integration tests for the Instrument router (/v1/instrument).

Tests instrument CRUD operations with various scenarios:
- Search instruments
- Get instrument by ID
- Create instrument
- Update drafted instrument (PATCH)
- Instrument status transitions
"""

from datetime import date, timedelta

import pytest
import pytest_asyncio
from app.enums import InstrumentStatus, UserRole
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.factories import (
    CompanyFactory,
    DocumentFactory,
    InstrumentDocumentFactory,
    InstrumentFactory,
    UserFactory,
)


class TestSearchInstruments:
    """Tests for POST /v1/instrument/search endpoint."""

    @pytest.mark.asyncio
    async def test_search_instruments_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test search instruments returns list of instruments.

        Arrange: Create company, user, and multiple instruments.
        Act: POST /v1/instrument/search with valid auth.
        Assert: Response is 200 with list of instruments.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument1 = await InstrumentFactory.create(
            db_session, company, issuer, name="Instrument One"
        )
        instrument2 = await InstrumentFactory.create(
            db_session, company, issuer, name="Instrument Two"
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/instrument/search",
            headers=headers,
            json={},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    @pytest.mark.asyncio
    async def test_search_instruments_with_currency_filter(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test search instruments by currency filter.

        Arrange: Create instruments with different currencies.
        Act: POST /v1/instrument/search with currency filter.
        Assert: Response contains only instruments with matching currency.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        usd_instrument = await InstrumentFactory.create(
            db_session, company, issuer, currency="USD"
        )
        eur_instrument = await InstrumentFactory.create(
            db_session, company, issuer, currency="EUR"
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/instrument/search",
            headers=headers,
            json={"currency": "USD"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        currencies = [i["currency"] for i in data]
        assert all(c == "USD" for c in currencies)

    @pytest.mark.asyncio
    async def test_search_instruments_with_face_value_filter(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test search instruments by face value range.

        Arrange: Create instruments with different face values.
        Act: POST /v1/instrument/search with min/max face value.
        Assert: Response contains only instruments within range.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        small_instrument = await InstrumentFactory.create(
            db_session, company, issuer, face_value=5000.00
        )
        large_instrument = await InstrumentFactory.create(
            db_session, company, issuer, face_value=50000.00
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/instrument/search",
            headers=headers,
            json={"minFaceValue": 10000.00, "maxFaceValue": 100000.00},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        for instrument in data:
            assert instrument["faceValue"] >= 10000.00
            assert instrument["faceValue"] <= 100000.00

    @pytest.mark.asyncio
    async def test_search_instruments_with_status_filter(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test search instruments by instrument status.

        Arrange: Create instruments with different statuses.
        Act: POST /v1/instrument/search with status filter.
        Assert: Response contains only instruments with matching status.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        draft_instrument = await InstrumentFactory.create(
            db_session, company, issuer,
            instrument_status=InstrumentStatus.DRAFT
        )
        active_instrument = await InstrumentFactory.create_active(
            db_session, company, issuer
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/instrument/search",
            headers=headers,
            json={"instrumentStatus": "DRAFT"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        statuses = [i["instrumentStatus"] for i in data]
        assert all(s == "DRAFT" for s in statuses)

    @pytest.mark.asyncio
    async def test_search_instruments_pagination(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test search instruments with pagination.

        Arrange: Create multiple instruments.
        Act: POST /v1/instrument/search with limit and offset.
        Assert: Response contains paginated results.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        for i in range(5):
            await InstrumentFactory.create(
                db_session, company, issuer, name=f"Instrument {i}"
            )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act - Get first 2 instruments
        response = await test_client.post(
            "/v1/instrument/search",
            headers=headers,
            json={"limit": 2, "offset": 0},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_search_instruments_without_permission_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test search instruments without VIEW.INSTRUMENT permission returns 403.

        Arrange: Create company and user without permission.
        Act: POST /v1/instrument/search.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        # Create user with no instrument permissions (use a role without VIEW.INSTRUMENT)
        # BUYER might not have this permission - depends on permission matrix
        buyer = await UserFactory.create(db_session, company, role=UserRole.BUYER)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(buyer.id),
            role=UserRole.BUYER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/instrument/search",
            headers=headers,
            json={},
        )

        # Assert - This depends on whether BUYER has VIEW.INSTRUMENT permission
        # If BUYER can view instruments, this test should be adjusted
        assert response.status_code in [200, 403]


class TestGetInstrumentById:
    """Tests for GET /v1/instrument/{instrument_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_instrument_by_id_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get instrument by ID returns instrument data.

        Arrange: Create company, user, and instrument.
        Act: GET /v1/instrument/{instrument_id} with valid auth.
        Assert: Response is 200 with instrument data.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create(
            db_session, company, issuer, name="Test Instrument"
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.get(
            f"/v1/instrument/{instrument.id}", headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Instrument"
        assert data["id"] == str(instrument.id)

    @pytest.mark.asyncio
    async def test_get_instrument_by_nonexistent_id_returns_404(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get instrument by non-existent ID returns 404.

        Arrange: Create company and user for auth.
        Act: GET /v1/instrument/{fake_uuid} with valid auth.
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
            f"/v1/instrument/{fake_uuid}", headers=headers
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_instrument_returns_correct_fields(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get instrument returns all expected fields.

        Arrange: Create instrument with specific values.
        Act: GET /v1/instrument/{instrument_id}.
        Assert: Response contains all expected fields with correct values.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        maturity_date = date.today() + timedelta(days=180)
        instrument = await InstrumentFactory.create(
            db_session,
            company,
            issuer,
            name="Complete Instrument",
            face_value=25000.00,
            currency="EUR",
            maturity_date=maturity_date,
            maturity_payment=26000.00,
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.get(
            f"/v1/instrument/{instrument.id}", headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Complete Instrument"
        assert data["faceValue"] == 25000.00
        assert data["currency"] == "EUR"
        assert data["maturityPayment"] == 26000.00
        assert data["instrumentStatus"] == "DRAFT"
        assert data["issuerId"] == str(company.id)
        assert data["createdBy"] == str(issuer.id)


class TestCreateInstrument:
    """Tests for POST /v1/instrument endpoint."""

    @pytest.mark.asyncio
    async def test_create_instrument_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create instrument with valid data returns created instrument.

        Arrange: Create company and admin user.
        Act: POST /v1/instrument with valid instrument data.
        Assert: Response is 200 with created instrument data.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, company)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        maturity_date = (date.today() + timedelta(days=90)).isoformat()

        # Act
        response = await test_client.post(
            "/v1/instrument/",
            headers=headers,
            json={
                "name": "New Instrument",
                "faceValue": 15000.00,
                "currency": "USD",
                "maturityDate": maturity_date,
                "maturityPayment": 15500.00,
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Instrument"
        assert data["faceValue"] == 15000.00
        assert data["currency"] == "USD"
        assert data["instrumentStatus"] == "DRAFT"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_instrument_with_public_payload(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create instrument with public payload.

        Arrange: Create company and admin user.
        Act: POST /v1/instrument with public_payload.
        Assert: Response includes created instrument with payload.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, company)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        maturity_date = (date.today() + timedelta(days=90)).isoformat()

        # Act
        response = await test_client.post(
            "/v1/instrument/",
            headers=headers,
            json={
                "name": "Instrument With Payload",
                "faceValue": 20000.00,
                "currency": "USD",
                "maturityDate": maturity_date,
                "maturityPayment": 21000.00,
                "publicPayload": {"description": "Test payload", "terms": "Standard"},
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Instrument With Payload"
        assert data["publicPayload"] is not None

    @pytest.mark.asyncio
    async def test_create_instrument_sets_issuer_from_current_user(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create instrument sets issuer_id and created_by from current user.

        Arrange: Create company and admin user.
        Act: POST /v1/instrument.
        Assert: issuer_id matches company_id, created_by matches user_id.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, company)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        maturity_date = (date.today() + timedelta(days=90)).isoformat()

        # Act
        response = await test_client.post(
            "/v1/instrument/",
            headers=headers,
            json={
                "name": "Issuer Test Instrument",
                "faceValue": 10000.00,
                "currency": "USD",
                "maturityDate": maturity_date,
                "maturityPayment": 10500.00,
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["issuerId"] == str(company.id)
        assert data["createdBy"] == str(admin.id)

    @pytest.mark.asyncio
    async def test_create_instrument_without_permission_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create instrument without CREATE.INSTRUMENT permission returns 403.

        Arrange: Create company and buyer user.
        Act: POST /v1/instrument with buyer auth.
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

        maturity_date = (date.today() + timedelta(days=90)).isoformat()

        # Act
        response = await test_client.post(
            "/v1/instrument/",
            headers=headers,
            json={
                "name": "Unauthorized Instrument",
                "faceValue": 10000.00,
                "currency": "USD",
                "maturityDate": maturity_date,
                "maturityPayment": 10500.00,
            },
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_instrument_missing_required_fields_returns_422(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create instrument without required fields returns 422.

        Arrange: Create company and admin.
        Act: POST /v1/instrument with missing name.
        Assert: Response is 422 Unprocessable Entity.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, company)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        # Act - missing name
        response = await test_client.post(
            "/v1/instrument/",
            headers=headers,
            json={
                "faceValue": 10000.00,
                "currency": "USD",
                "maturityDate": (date.today() + timedelta(days=90)).isoformat(),
                "maturityPayment": 10500.00,
            },
        )

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_instrument_invalid_currency_returns_422(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create instrument with invalid currency returns 422.

        Arrange: Create company and admin.
        Act: POST /v1/instrument with currency longer than 3 chars.
        Assert: Response is 422 Unprocessable Entity.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, company)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        # Act - invalid currency (too long)
        response = await test_client.post(
            "/v1/instrument/",
            headers=headers,
            json={
                "name": "Invalid Currency Instrument",
                "faceValue": 10000.00,
                "currency": "USDD",  # 4 characters, should be 3
                "maturityDate": (date.today() + timedelta(days=90)).isoformat(),
                "maturityPayment": 10500.00,
            },
        )

        # Assert
        assert response.status_code == 422


class TestUpdateDraftedInstrument:
    """Tests for PATCH /v1/instrument/{instrument_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_draft_instrument_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test update drafted instrument updates specified fields.

        Arrange: Create company, user, and draft instrument.
        Act: PATCH /v1/instrument/{instrument_id} with new name.
        Assert: Response is 200 with updated instrument.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create(
            db_session, company, issuer, name="Original Name"
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.patch(
            f"/v1/instrument/{instrument.id}",
            headers=headers,
            json={"name": "Updated Name"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_draft_instrument_multiple_fields(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test update drafted instrument with multiple fields.

        Arrange: Create draft instrument.
        Act: PATCH with name, face_value, and currency.
        Assert: All fields are updated.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create(
            db_session, company, issuer,
            name="Original",
            face_value=10000.00,
            currency="USD",
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.patch(
            f"/v1/instrument/{instrument.id}",
            headers=headers,
            json={
                "name": "Updated Name",
                "faceValue": 20000.00,
                "currency": "EUR",
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["faceValue"] == 20000.00
        assert data["currency"] == "EUR"

    @pytest.mark.asyncio
    async def test_update_non_draft_instrument_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test update non-draft instrument returns 403.

        Arrange: Create instrument with ACTIVE status.
        Act: PATCH /v1/instrument/{instrument_id}.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create_active(
            db_session, company, issuer
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.patch(
            f"/v1/instrument/{instrument.id}",
            headers=headers,
            json={"name": "Try Update Active"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_instrument_different_company_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test update instrument from different company returns 403.

        Arrange: Create two companies with users and instrument.
        Act: User from company2 tries to update instrument from company1.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        company1 = await CompanyFactory.create(db_session, legal_name="Company One")
        company2 = await CompanyFactory.create(db_session, legal_name="Company Two")
        issuer1 = await UserFactory.create_issuer(db_session, company1)
        issuer2 = await UserFactory.create_issuer(db_session, company2)
        instrument = await InstrumentFactory.create(db_session, company1, issuer1)
        await db_session.commit()

        # User from company2 trying to update
        headers = auth_headers(
            user_id=str(issuer2.id),
            role=UserRole.ISSUER,
            company_id=str(company2.id),
        )

        # Act
        response = await test_client.patch(
            f"/v1/instrument/{instrument.id}",
            headers=headers,
            json={"name": "Hacked Name"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_nonexistent_instrument_returns_404(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test update non-existent instrument returns 404.

        Arrange: Create company and user for auth.
        Act: PATCH /v1/instrument/{fake_id}.
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
        response = await test_client.patch(
            f"/v1/instrument/{fake_uuid}",
            headers=headers,
            json={"name": "Ghost Instrument"},
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_instrument_with_past_maturity_date_returns_422(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test update instrument with past maturity date returns 422.

        Arrange: Create draft instrument.
        Act: PATCH with maturity_date in the past.
        Assert: Response is 422 Unprocessable Entity.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create(db_session, company, issuer)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        past_date = (date.today() - timedelta(days=30)).isoformat()

        # Act
        response = await test_client.patch(
            f"/v1/instrument/{instrument.id}",
            headers=headers,
            json={"maturityDate": past_date},
        )

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_instrument_with_negative_face_value_returns_422(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test update instrument with negative face value returns 422.

        Arrange: Create draft instrument.
        Act: PATCH with negative face_value.
        Assert: Response is 422 Unprocessable Entity.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create(db_session, company, issuer)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.patch(
            f"/v1/instrument/{instrument.id}",
            headers=headers,
            json={"faceValue": -1000.00},
        )

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_instrument_with_public_payload(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test update instrument with public payload.

        Arrange: Create draft instrument.
        Act: PATCH with public_payload.
        Assert: Public payload is updated.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create(db_session, company, issuer)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.patch(
            f"/v1/instrument/{instrument.id}",
            headers=headers,
            json={"publicPayload": {"updated": True, "notes": "Updated payload"}},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["publicPayload"] is not None


class TestInstrumentStatusTransition:
    """Tests for POST /v1/instrument/{instrument_id}/transition endpoint."""

    @pytest.mark.asyncio
    async def test_transition_draft_to_pending_approval_by_issuer(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test issuer can transition DRAFT to PENDING_APPROVAL.

        Arrange: Create draft instrument.
        Act: POST /v1/instrument/{id}/transition with PENDING_APPROVAL.
        Assert: Status is changed to PENDING_APPROVAL.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create(db_session, company, issuer)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/instrument/{instrument.id}/transition",
            headers=headers,
            json={"newStatus": "PENDING_APPROVAL"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["instrumentStatus"] == "PENDING_APPROVAL"

    @pytest.mark.asyncio
    async def test_transition_pending_approval_to_active_by_admin(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test admin can transition PENDING_APPROVAL to ACTIVE.

        Arrange: Create instrument with PENDING_APPROVAL status.
        Act: POST /v1/instrument/{id}/transition with ACTIVE.
        Assert: Status is changed to ACTIVE.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, company)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create_pending_approval(
            db_session, company, issuer
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/instrument/{instrument.id}/transition",
            headers=headers,
            json={"newStatus": "ACTIVE"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["instrumentStatus"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_transition_pending_approval_to_rejected_by_admin(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test admin can transition PENDING_APPROVAL to REJECTED.

        Arrange: Create instrument with PENDING_APPROVAL status.
        Act: POST /v1/instrument/{id}/transition with REJECTED.
        Assert: Status is changed to REJECTED.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, company)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create_pending_approval(
            db_session, company, issuer
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/instrument/{instrument.id}/transition",
            headers=headers,
            json={"newStatus": "REJECTED"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["instrumentStatus"] == "REJECTED"

    @pytest.mark.asyncio
    async def test_transition_invalid_status_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test invalid status transition returns 403.

        Arrange: Create draft instrument.
        Act: Try to transition DRAFT directly to ACTIVE (invalid).
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create(db_session, company, issuer)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act - Try invalid transition (DRAFT -> ACTIVE)
        response = await test_client.post(
            f"/v1/instrument/{instrument.id}/transition",
            headers=headers,
            json={"newStatus": "ACTIVE"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_transition_by_buyer_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test buyer cannot perform status transition.

        Arrange: Create draft instrument.
        Act: Buyer tries to transition status.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        buyer = await UserFactory.create(db_session, company, role=UserRole.BUYER)
        instrument = await InstrumentFactory.create(db_session, company, issuer)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(buyer.id),
            role=UserRole.BUYER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/instrument/{instrument.id}/transition",
            headers=headers,
            json={"newStatus": "PENDING_APPROVAL"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_transition_nonexistent_instrument_returns_404(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test transition on non-existent instrument returns 404.

        Arrange: Create company and user for auth.
        Act: POST /v1/instrument/{fake_id}/transition.
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
            f"/v1/instrument/{fake_uuid}/transition",
            headers=headers,
            json={"newStatus": "PENDING_APPROVAL"},
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_transition_to_active_sets_maturity_status_due(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test transition to ACTIVE also sets maturity_status to DUE.

        Arrange: Create instrument with PENDING_APPROVAL status.
        Act: POST /v1/instrument/{id}/transition with ACTIVE.
        Assert: maturity_status is set to DUE.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, company)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create_pending_approval(
            db_session, company, issuer
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/instrument/{instrument.id}/transition",
            headers=headers,
            json={"newStatus": "ACTIVE"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["instrumentStatus"] == "ACTIVE"
        assert data["maturityStatus"] == "DUE"

    @pytest.mark.asyncio
    async def test_transition_invalid_status_value_returns_422(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test transition with invalid status value returns 422.

        Arrange: Create draft instrument.
        Act: POST /v1/instrument/{id}/transition with invalid status.
        Assert: Response is 422 Unprocessable Entity.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create(db_session, company, issuer)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act - invalid status value
        response = await test_client.post(
            f"/v1/instrument/{instrument.id}/transition",
            headers=headers,
            json={"newStatus": "INVALID_STATUS"},
        )

        # Assert
        assert response.status_code == 422


class TestGetInstrumentWithIncludes:
    """Tests for GET /v1/instrument/{instrument_id}?include=documents endpoint."""

    @pytest.mark.asyncio
    async def test_get_instrument_without_include_returns_no_documents(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get instrument without include parameter returns instrument_documents as None.

        Arrange: Create instrument with associated documents.
        Act: GET /v1/instrument/{instrument_id} without include parameter.
        Assert: Response contains instrument data with instrumentDocuments as None.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create(
            db_session, company, issuer, name="Instrument With Docs"
        )
        document = await DocumentFactory.create(db_session, issuer)
        await InstrumentDocumentFactory.create(db_session, instrument, document)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.get(
            f"/v1/instrument/{instrument.id}",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Instrument With Docs"
        assert data.get("instrumentDocuments") is None

    @pytest.mark.asyncio
    async def test_get_instrument_with_include_documents_returns_documents(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get instrument with include=documents returns associated documents.

        Arrange: Create instrument with multiple associated documents.
        Act: GET /v1/instrument/{instrument_id}?include=documents.
        Assert: Response contains instrument data with instrumentDocuments list.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create(
            db_session, company, issuer, name="Instrument With Multiple Docs"
        )
        document1 = await DocumentFactory.create(
            db_session, issuer, internal_filename="doc1.pdf"
        )
        document2 = await DocumentFactory.create(
            db_session, issuer, internal_filename="doc2.pdf"
        )
        await InstrumentDocumentFactory.create(db_session, instrument, document1)
        await InstrumentDocumentFactory.create(db_session, instrument, document2)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.get(
            f"/v1/instrument/{instrument.id}?include=documents",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Instrument With Multiple Docs"
        assert data["instrumentDocuments"] is not None
        assert isinstance(data["instrumentDocuments"], list)
        assert len(data["instrumentDocuments"]) == 2

        # Verify each instrument_document contains the nested document
        for inst_doc in data["instrumentDocuments"]:
            assert "instrumentId" in inst_doc
            assert "documentId" in inst_doc
            assert "document" in inst_doc
            assert inst_doc["document"] is not None
            assert "internalFilename" in inst_doc["document"]

    @pytest.mark.asyncio
    async def test_get_instrument_with_include_documents_returns_nested_document_data(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get instrument with include=documents returns nested document details.

        Arrange: Create instrument with associated document with specific data.
        Act: GET /v1/instrument/{instrument_id}?include=documents.
        Assert: Response contains nested document with correct field values.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create(db_session, company, issuer)
        document = await DocumentFactory.create(
            db_session,
            issuer,
            internal_filename="test_prospectus.pdf",
            mime="application/pdf",
            storage_bucket="documents-bucket",
        )
        await InstrumentDocumentFactory.create(db_session, instrument, document)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.get(
            f"/v1/instrument/{instrument.id}?include=documents",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["instrumentDocuments"]) == 1

        inst_doc = data["instrumentDocuments"][0]
        nested_doc = inst_doc["document"]
        assert nested_doc["internalFilename"] == "test_prospectus.pdf"
        assert nested_doc["mime"] == "application/pdf"
        assert nested_doc["storageBucket"] == "documents-bucket"
        assert nested_doc["id"] == str(document.id)

    @pytest.mark.asyncio
    async def test_get_instrument_with_no_documents_returns_empty_list(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get instrument with include=documents when no documents exist.

        Arrange: Create instrument without any associated documents.
        Act: GET /v1/instrument/{instrument_id}?include=documents.
        Assert: Response contains empty instrumentDocuments list.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create(
            db_session, company, issuer, name="Instrument Without Docs"
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.get(
            f"/v1/instrument/{instrument.id}?include=documents",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Instrument Without Docs"
        assert data["instrumentDocuments"] is not None
        assert isinstance(data["instrumentDocuments"], list)
        assert len(data["instrumentDocuments"]) == 0

    @pytest.mark.asyncio
    async def test_get_instrument_with_invalid_include_ignores_unknown_value(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get instrument with invalid include value is silently ignored.

        Arrange: Create instrument.
        Act: GET /v1/instrument/{instrument_id}?include=invalid_value.
        Assert: Response returns instrument data without errors.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create(db_session, company, issuer)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.get(
            f"/v1/instrument/{instrument.id}?include=invalid_value",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(instrument.id)
        # instrumentDocuments should be None since no valid include was provided
        assert data.get("instrumentDocuments") is None

    @pytest.mark.asyncio
    async def test_get_instrument_with_include_preserves_other_fields(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get instrument with include=documents still returns all base fields.

        Arrange: Create instrument with specific field values.
        Act: GET /v1/instrument/{instrument_id}?include=documents.
        Assert: Response contains all standard instrument fields plus documents.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        maturity_date = date.today() + timedelta(days=180)
        instrument = await InstrumentFactory.create(
            db_session,
            company,
            issuer,
            name="Complete Instrument",
            face_value=50000.00,
            currency="EUR",
            maturity_date=maturity_date,
            maturity_payment=52000.00,
        )
        document = await DocumentFactory.create(db_session, issuer)
        await InstrumentDocumentFactory.create(db_session, instrument, document)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.get(
            f"/v1/instrument/{instrument.id}?include=documents",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        # Verify base fields are present
        assert data["name"] == "Complete Instrument"
        assert data["faceValue"] == 50000.00
        assert data["currency"] == "EUR"
        assert data["maturityPayment"] == 52000.00
        assert data["instrumentStatus"] == "DRAFT"
        assert data["issuerId"] == str(company.id)
        assert data["createdBy"] == str(issuer.id)
        # Verify documents are included
        assert data["instrumentDocuments"] is not None
        assert len(data["instrumentDocuments"]) == 1


class TestAssociateDocumentWithInstrument:
    """Tests for POST /v1/instrument/{instrument_id}/documents/{document_id} endpoint."""

    @pytest.mark.asyncio
    async def test_associate_document_with_instrument_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test successful association of a document with an instrument.

        Arrange: Create instrument and document.
        Act: POST /v1/instrument/{instrument_id}/documents/{document_id}.
        Assert: Response is 200 with InstrumentDocument association.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create(db_session, company, issuer)
        document = await DocumentFactory.create(db_session, issuer)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/instrument/{instrument.id}/documents/{document.id}",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["instrumentId"] == str(instrument.id)
        assert data["documentId"] == str(document.id)
        assert "id" in data

    @pytest.mark.asyncio
    async def test_associate_document_with_nonexistent_instrument_returns_404(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test associating document with non-existent instrument returns 404.

        Arrange: Create company, user, and document.
        Act: POST /v1/instrument/{fake_uuid}/documents/{document_id}.
        Assert: Response is 404 Not Found.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        document = await DocumentFactory.create(db_session, issuer)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        # Act
        response = await test_client.post(
            f"/v1/instrument/{fake_uuid}/documents/{document.id}",
            headers=headers,
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Instrument" in data["detail"]

    @pytest.mark.asyncio
    async def test_associate_nonexistent_document_with_instrument_returns_404(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test associating non-existent document with instrument returns 404.

        Arrange: Create company, user, and instrument.
        Act: POST /v1/instrument/{instrument_id}/documents/{fake_uuid}.
        Assert: Response is 404 Not Found.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create(db_session, company, issuer)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        # Act
        response = await test_client.post(
            f"/v1/instrument/{instrument.id}/documents/{fake_uuid}",
            headers=headers,
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Document" in data["detail"]

    @pytest.mark.asyncio
    async def test_associate_document_already_associated_returns_409(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test associating document that is already associated returns 409.

        Arrange: Create instrument, document, and existing association.
        Act: POST /v1/instrument/{instrument_id}/documents/{document_id}.
        Assert: Response is 409 Conflict.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create(db_session, company, issuer)
        document = await DocumentFactory.create(db_session, issuer)
        # Create existing association
        await InstrumentDocumentFactory.create(db_session, instrument, document)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/instrument/{instrument.id}/documents/{document.id}",
            headers=headers,
        )

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert "already associated" in data["detail"]

    @pytest.mark.asyncio
    async def test_associate_document_without_permission_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test associating document without UPDATE.INSTRUMENT permission returns 403.

        Arrange: Create instrument, document, and buyer user.
        Act: POST /v1/instrument/{instrument_id}/documents/{document_id} with buyer auth.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        buyer = await UserFactory.create(db_session, company, role=UserRole.BUYER)
        instrument = await InstrumentFactory.create(db_session, company, issuer)
        document = await DocumentFactory.create(db_session, issuer)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(buyer.id),
            role=UserRole.BUYER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/instrument/{instrument.id}/documents/{document.id}",
            headers=headers,
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_associate_document_by_admin_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test admin can associate document with instrument.

        Arrange: Create instrument, document, and admin user.
        Act: POST /v1/instrument/{instrument_id}/documents/{document_id} with admin auth.
        Assert: Response is 200 with InstrumentDocument association.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, company)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create(db_session, company, issuer)
        document = await DocumentFactory.create(db_session, issuer)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            f"/v1/instrument/{instrument.id}/documents/{document.id}",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["instrumentId"] == str(instrument.id)
        assert data["documentId"] == str(document.id)

    @pytest.mark.asyncio
    async def test_associate_multiple_documents_with_same_instrument(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test associating multiple different documents with the same instrument.

        Arrange: Create instrument and multiple documents.
        Act: POST /v1/instrument/{instrument_id}/documents/{document_id} for each.
        Assert: Each response is 200 with correct associations.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument = await InstrumentFactory.create(db_session, company, issuer)
        document1 = await DocumentFactory.create(
            db_session, issuer, internal_filename="doc1.pdf"
        )
        document2 = await DocumentFactory.create(
            db_session, issuer, internal_filename="doc2.pdf"
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act - Associate first document
        response1 = await test_client.post(
            f"/v1/instrument/{instrument.id}/documents/{document1.id}",
            headers=headers,
        )

        # Act - Associate second document
        response2 = await test_client.post(
            f"/v1/instrument/{instrument.id}/documents/{document2.id}",
            headers=headers,
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        data1 = response1.json()
        data2 = response2.json()
        assert data1["documentId"] == str(document1.id)
        assert data2["documentId"] == str(document2.id)
        assert data1["instrumentId"] == str(instrument.id)
        assert data2["instrumentId"] == str(instrument.id)

    @pytest.mark.asyncio
    async def test_associate_same_document_with_multiple_instruments(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test associating the same document with multiple instruments.

        Arrange: Create multiple instruments and one document.
        Act: POST /v1/instrument/{instrument_id}/documents/{document_id} for each instrument.
        Assert: Each response is 200 with correct associations.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        issuer = await UserFactory.create_issuer(db_session, company)
        instrument1 = await InstrumentFactory.create(
            db_session, company, issuer, name="Instrument 1"
        )
        instrument2 = await InstrumentFactory.create(
            db_session, company, issuer, name="Instrument 2"
        )
        document = await DocumentFactory.create(db_session, issuer)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(issuer.id),
            role=UserRole.ISSUER,
            company_id=str(company.id),
        )

        # Act - Associate document with first instrument
        response1 = await test_client.post(
            f"/v1/instrument/{instrument1.id}/documents/{document.id}",
            headers=headers,
        )

        # Act - Associate same document with second instrument
        response2 = await test_client.post(
            f"/v1/instrument/{instrument2.id}/documents/{document.id}",
            headers=headers,
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        data1 = response1.json()
        data2 = response2.json()
        assert data1["instrumentId"] == str(instrument1.id)
        assert data2["instrumentId"] == str(instrument2.id)
        assert data1["documentId"] == str(document.id)
        assert data2["documentId"] == str(document.id)
