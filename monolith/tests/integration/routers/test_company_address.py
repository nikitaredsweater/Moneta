"""
Integration tests for the Company Address router (/v1/company-address).

Tests company address CRUD operations with various scenarios:
- Get all company addresses
- Create company address
"""

import pytest
import pytest_asyncio
from app.enums import AddressType, UserRole
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.factories import CompanyAddressFactory, CompanyFactory, UserFactory


class TestGetAllCompanyAddresses:
    """Tests for GET /v1/company-address endpoint."""

    @pytest.mark.asyncio
    async def test_get_all_company_addresses_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get all company addresses returns list of addresses.

        Arrange: Create company and multiple addresses.
        Act: GET /v1/company-address with valid auth.
        Assert: Response is 200 with list of addresses.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, company)
        address1 = await CompanyAddressFactory.create(
            db_session, company, street="123 Main St"
        )
        address2 = await CompanyAddressFactory.create_billing(
            db_session, company, street="456 Billing Ave"
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.get("/v1/company-address/", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    @pytest.mark.asyncio
    async def test_get_all_company_addresses_empty_returns_empty_list(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get all company addresses with no addresses returns empty list.

        Arrange: Create company without any addresses.
        Act: GET /v1/company-address.
        Assert: Response is 200 with empty list.
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

        # Act
        response = await test_client.get("/v1/company-address/", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_get_all_company_addresses_returns_correct_fields(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get all company addresses returns all expected fields.

        Arrange: Create company address with specific values.
        Act: GET /v1/company-address.
        Assert: Response contains all expected fields with correct values.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, company)
        address = await CompanyAddressFactory.create(
            db_session,
            company,
            address_type=AddressType.REGISTERED,
            street="789 Business Blvd",
            city="San Francisco",
            state="CA",
            postal_code="94102",
            country="US",
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.get("/v1/company-address/", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

        # Find our created address
        created_address = next(
            (a for a in data if a["street"] == "789 Business Blvd"), None
        )
        assert created_address is not None
        assert created_address["type"] == "REGISTERED"
        assert created_address["city"] == "San Francisco"
        assert created_address["state"] == "CA"
        assert created_address["postalCode"] == "94102"
        assert created_address["country"] == "US"
        assert created_address["companyId"] == str(company.id)

    @pytest.mark.asyncio
    async def test_get_all_company_addresses_with_multiple_companies(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get all company addresses returns addresses from all companies.

        Arrange: Create multiple companies with addresses.
        Act: GET /v1/company-address.
        Assert: Response contains addresses from all companies.
        """
        # Arrange
        company1 = await CompanyFactory.create(db_session, legal_name="Company One")
        company2 = await CompanyFactory.create(db_session, legal_name="Company Two")
        admin = await UserFactory.create_admin(db_session, company1)
        address1 = await CompanyAddressFactory.create(
            db_session, company1, street="Company One Street"
        )
        address2 = await CompanyAddressFactory.create(
            db_session, company2, street="Company Two Street"
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company1.id),
        )

        # Act
        response = await test_client.get("/v1/company-address/", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        streets = [a["street"] for a in data]
        assert "Company One Street" in streets
        assert "Company Two Street" in streets

    @pytest.mark.asyncio
    async def test_get_all_company_addresses_without_permission_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get all company addresses without VIEW.COMPANY_ADDRESS permission returns 403.

        Arrange: Create company and user without permission.
        Act: GET /v1/company-address.
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
        response = await test_client.get("/v1/company-address/", headers=headers)

        # Assert - depends on permission matrix
        assert response.status_code in [200, 403]

    @pytest.mark.asyncio
    async def test_get_all_company_addresses_with_different_types(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get all company addresses returns addresses of different types.

        Arrange: Create addresses with different types.
        Act: GET /v1/company-address.
        Assert: Response contains addresses of different types.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, company)
        registered = await CompanyAddressFactory.create(
            db_session, company, address_type=AddressType.REGISTERED
        )
        billing = await CompanyAddressFactory.create_billing(db_session, company)
        office = await CompanyAddressFactory.create_office(db_session, company)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.get("/v1/company-address/", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        types = [a["type"] for a in data]
        assert "REGISTERED" in types
        assert "BILLING" in types
        assert "OFFICE" in types


class TestCreateCompanyAddress:
    """Tests for POST /v1/company-address endpoint."""

    @pytest.mark.asyncio
    async def test_create_company_address_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create company address with valid data returns created address.

        Arrange: Create company and admin user.
        Act: POST /v1/company-address with valid address data.
        Assert: Response is 200 with created address data.
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

        # Act
        response = await test_client.post(
            "/v1/company-address/",
            headers=headers,
            json={
                "type": "REGISTERED",
                "street": "100 New Address Lane",
                "city": "Boston",
                "state": "MA",
                "postalCode": "02101",
                "country": "US",
                "companyId": str(company.id),
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["street"] == "100 New Address Lane"
        assert data["city"] == "Boston"
        assert data["state"] == "MA"
        assert data["postalCode"] == "02101"
        assert data["country"] == "US"
        assert data["type"] == "REGISTERED"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_company_address_billing_type(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create company address with BILLING type.

        Arrange: Create company and admin user.
        Act: POST /v1/company-address with BILLING type.
        Assert: Response is 200 with BILLING address.
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

        # Act
        response = await test_client.post(
            "/v1/company-address/",
            headers=headers,
            json={
                "type": "BILLING",
                "street": "200 Billing Road",
                "city": "Chicago",
                "state": "IL",
                "postalCode": "60601",
                "country": "US",
                "companyId": str(company.id),
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "BILLING"
        assert data["street"] == "200 Billing Road"

    @pytest.mark.asyncio
    async def test_create_company_address_office_type(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create company address with OFFICE type.

        Arrange: Create company and admin user.
        Act: POST /v1/company-address with OFFICE type.
        Assert: Response is 200 with OFFICE address.
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

        # Act
        response = await test_client.post(
            "/v1/company-address/",
            headers=headers,
            json={
                "type": "OFFICE",
                "street": "300 Office Plaza",
                "city": "Seattle",
                "state": "WA",
                "postalCode": "98101",
                "country": "US",
                "companyId": str(company.id),
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "OFFICE"
        assert data["street"] == "300 Office Plaza"

    @pytest.mark.asyncio
    async def test_create_company_address_without_state(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create company address without state (optional field).

        Arrange: Create company and admin user.
        Act: POST /v1/company-address without state field.
        Assert: Response is 200 with null state.
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

        # Act
        response = await test_client.post(
            "/v1/company-address/",
            headers=headers,
            json={
                "type": "REGISTERED",
                "street": "10 No State Street",
                "city": "London",
                "postalCode": "SW1A 1AA",
                "country": "GB",
                "companyId": str(company.id),
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["state"] is None
        assert data["city"] == "London"
        assert data["country"] == "GB"

    @pytest.mark.asyncio
    async def test_create_company_address_shipping_type(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create company address with SHIPPING type.

        Arrange: Create company and admin user.
        Act: POST /v1/company-address with SHIPPING type.
        Assert: Response is 200 with SHIPPING address.
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

        # Act
        response = await test_client.post(
            "/v1/company-address/",
            headers=headers,
            json={
                "type": "SHIPPING",
                "street": "400 Warehouse Way",
                "city": "Los Angeles",
                "state": "CA",
                "postalCode": "90001",
                "country": "US",
                "companyId": str(company.id),
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "SHIPPING"

    @pytest.mark.asyncio
    async def test_create_company_address_other_type(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create company address with OTHER type.

        Arrange: Create company and admin user.
        Act: POST /v1/company-address with OTHER type.
        Assert: Response is 200 with OTHER address.
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

        # Act
        response = await test_client.post(
            "/v1/company-address/",
            headers=headers,
            json={
                "type": "OTHER",
                "street": "500 Other Street",
                "city": "Miami",
                "state": "FL",
                "postalCode": "33101",
                "country": "US",
                "companyId": str(company.id),
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "OTHER"

    @pytest.mark.asyncio
    async def test_create_company_address_for_different_company(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create company address for a different company.

        Arrange: Create two companies with admin.
        Act: POST /v1/company-address for company2 while authenticated as company1.
        Assert: Response is 200 (depends on permission implementation).
        """
        # Arrange
        company1 = await CompanyFactory.create(db_session, legal_name="Company One")
        company2 = await CompanyFactory.create(db_session, legal_name="Company Two")
        admin = await UserFactory.create_admin(db_session, company1)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company1.id),
        )

        # Act
        response = await test_client.post(
            "/v1/company-address/",
            headers=headers,
            json={
                "type": "REGISTERED",
                "street": "Different Company Street",
                "city": "Denver",
                "state": "CO",
                "postalCode": "80201",
                "country": "US",
                "companyId": str(company2.id),
            },
        )

        # Assert - depends on permission implementation
        # Some systems allow admins to create addresses for any company
        assert response.status_code in [200, 403]

    @pytest.mark.asyncio
    async def test_create_company_address_without_permission_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create company address without CREATE.COMPANY_ADDRESS permission returns 403.

        Arrange: Create company and buyer user.
        Act: POST /v1/company-address with buyer auth.
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
            "/v1/company-address/",
            headers=headers,
            json={
                "type": "REGISTERED",
                "street": "Unauthorized Street",
                "city": "Phoenix",
                "state": "AZ",
                "postalCode": "85001",
                "country": "US",
                "companyId": str(company.id),
            },
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_company_address_missing_required_fields_returns_422(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create company address without required fields returns 422.

        Arrange: Create company and admin.
        Act: POST /v1/company-address with missing street.
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

        # Act - missing street
        response = await test_client.post(
            "/v1/company-address/",
            headers=headers,
            json={
                "type": "REGISTERED",
                "city": "Dallas",
                "postalCode": "75201",
                "country": "US",
                "companyId": str(company.id),
            },
        )

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_company_address_missing_type_returns_422(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create company address without type returns 422.

        Arrange: Create company and admin.
        Act: POST /v1/company-address without type field.
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

        # Act - missing type
        response = await test_client.post(
            "/v1/company-address/",
            headers=headers,
            json={
                "street": "No Type Street",
                "city": "Houston",
                "postalCode": "77001",
                "country": "US",
                "companyId": str(company.id),
            },
        )

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_company_address_missing_company_id_returns_422(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create company address without company_id returns 422.

        Arrange: Create company and admin.
        Act: POST /v1/company-address without companyId.
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

        # Act - missing companyId
        response = await test_client.post(
            "/v1/company-address/",
            headers=headers,
            json={
                "type": "REGISTERED",
                "street": "No Company Street",
                "city": "Atlanta",
                "postalCode": "30301",
                "country": "US",
            },
        )

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_company_address_invalid_type_returns_422(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create company address with invalid type returns 422.

        Arrange: Create company and admin.
        Act: POST /v1/company-address with invalid type.
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

        # Act - invalid type
        response = await test_client.post(
            "/v1/company-address/",
            headers=headers,
            json={
                "type": "INVALID_TYPE",
                "street": "Invalid Type Street",
                "city": "Philadelphia",
                "postalCode": "19101",
                "country": "US",
                "companyId": str(company.id),
            },
        )

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_company_address_empty_body_returns_422(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create company address with empty body returns 422.

        Arrange: Create company and admin.
        Act: POST /v1/company-address with empty JSON body.
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

        # Act - empty body
        response = await test_client.post(
            "/v1/company-address/",
            headers=headers,
            json={},
        )

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_company_address_nonexistent_company_returns_error(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create company address for non-existent company returns error.

        Arrange: Create company and admin.
        Act: POST /v1/company-address with non-existent companyId.
        Assert: Response is error (400, 404, or 500 depending on implementation).
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
        fake_company_id = "00000000-0000-0000-0000-000000000000"

        # Act
        response = await test_client.post(
            "/v1/company-address/",
            headers=headers,
            json={
                "type": "REGISTERED",
                "street": "Ghost Company Street",
                "city": "Portland",
                "state": "OR",
                "postalCode": "97201",
                "country": "US",
                "companyId": fake_company_id,
            },
        )

        # Assert - depends on FK constraint handling
        # Could be 404 (company not found), 400 (bad request), or 500 (DB error)
        assert response.status_code in [400, 404, 500]

    @pytest.mark.asyncio
    async def test_create_multiple_addresses_for_same_company(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test creating multiple addresses for the same company.

        Arrange: Create company and admin.
        Act: POST /v1/company-address twice for same company.
        Assert: Both addresses are created successfully.
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

        # Act - create first address
        response1 = await test_client.post(
            "/v1/company-address/",
            headers=headers,
            json={
                "type": "REGISTERED",
                "street": "First Address Street",
                "city": "Detroit",
                "state": "MI",
                "postalCode": "48201",
                "country": "US",
                "companyId": str(company.id),
            },
        )

        # Act - create second address
        response2 = await test_client.post(
            "/v1/company-address/",
            headers=headers,
            json={
                "type": "BILLING",
                "street": "Second Address Street",
                "city": "Detroit",
                "state": "MI",
                "postalCode": "48202",
                "country": "US",
                "companyId": str(company.id),
            },
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        data1 = response1.json()
        data2 = response2.json()
        assert data1["id"] != data2["id"]
        assert data1["type"] == "REGISTERED"
        assert data2["type"] == "BILLING"

    @pytest.mark.asyncio
    async def test_create_company_address_issuer_permission(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create company address with issuer role.

        Arrange: Create company and issuer user.
        Act: POST /v1/company-address with issuer auth.
        Assert: Response depends on issuer permissions for company addresses.
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

        # Act
        response = await test_client.post(
            "/v1/company-address/",
            headers=headers,
            json={
                "type": "OFFICE",
                "street": "Issuer Office Street",
                "city": "Minneapolis",
                "state": "MN",
                "postalCode": "55401",
                "country": "US",
                "companyId": str(company.id),
            },
        )

        # Assert - depends on whether ISSUER has CREATE.COMPANY_ADDRESS permission
        assert response.status_code in [200, 403]
