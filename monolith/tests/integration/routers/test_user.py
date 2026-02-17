"""
Integration tests for the User router (/v1/user).

Tests user CRUD operations with various scenarios:
- Get all users (with permission)
- Get user by ID
- Create user
- Update user (PATCH)
- Delete user
- Search users
"""

import pytest
import pytest_asyncio
from app.enums import ActivationStatus, UserRole
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.factories import CompanyFactory, UserFactory


class TestGetAllUsers:
    """Tests for GET /v1/user endpoint."""

    @pytest.mark.asyncio
    async def test_get_all_users_with_admin_permission(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test admin can get all users.

        Arrange: Create company and admin user, plus additional users.
        Act: GET /v1/user with admin auth headers.
        Assert: Response is 200 with list of users.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, company)
        user1 = await UserFactory.create(
            db_session, company, email="user1@example.com"
        )
        user2 = await UserFactory.create(
            db_session, company, email="user2@example.com"
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.get("/v1/user/", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3  # admin + 2 users

    @pytest.mark.asyncio
    async def test_get_all_users_without_permission_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test non-admin cannot get all users.

        Arrange: Create company and buyer user.
        Act: GET /v1/user with buyer auth headers.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        buyer = await UserFactory.create(
            db_session, company, role=UserRole.BUYER
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(buyer.id),
            role=UserRole.BUYER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.get("/v1/user/", headers=headers)

        # Assert
        assert response.status_code == 403


class TestGetUserById:
    """Tests for GET /v1/user/{user_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get user by ID returns user data.

        Arrange: Create company and user.
        Act: GET /v1/user/{user_id} with valid auth.
        Assert: Response is 200 with user data.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        user = await UserFactory.create(
            db_session,
            company,
            email="findme@example.com",
            first_name="Find",
            last_name="Me",
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(user.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.get(f"/v1/user/{user.id}", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "findme@example.com"
        assert data["firstName"] == "Find"
        assert data["lastName"] == "Me"

    @pytest.mark.asyncio
    async def test_get_user_by_nonexistent_id_returns_none(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test get user by non-existent ID returns null.

        Arrange: Create company and user for auth.
        Act: GET /v1/user/{random_uuid} with valid auth.
        Assert: Response is 200 with null body.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        user = await UserFactory.create(db_session, company)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(user.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        # Act
        response = await test_client.get(
            f"/v1/user/{fake_uuid}", headers=headers
        )

        # Assert
        assert response.status_code == 200
        assert response.json() is None


class TestCreateUser:
    """Tests for POST /v1/user endpoint."""

    @pytest.mark.asyncio
    async def test_create_user_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create user with valid data returns created user.

        Arrange: Create company and admin user.
        Act: POST /v1/user with valid user data.
        Assert: Response is 200 with created user data.
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
            "/v1/user/",
            headers=headers,
            json={
                "email": "newuser@example.com",
                "password": "NewUserPassword123!",
                "firstName": "New",
                "lastName": "User",
                "companyId": str(company.id),
                "role": "BUYER",
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["firstName"] == "New"
        assert data["lastName"] == "User"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email_returns_409(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create user with existing email returns 409 conflict.

        Arrange: Create company, admin, and existing user.
        Act: POST /v1/user with duplicate email.
        Assert: Response is 409 Conflict.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, company)
        existing_user = await UserFactory.create(
            db_session, company, email="existing@example.com"
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/user/",
            headers=headers,
            json={
                "email": "existing@example.com",  # Duplicate
                "password": "NewPassword123!",
                "firstName": "Duplicate",
                "lastName": "User",
                "companyId": str(company.id),
                "role": "BUYER",
            },
        )

        # Assert
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_user_nonexistent_company_returns_404(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create user with non-existent company ID returns 404.

        Arrange: Create company and admin.
        Act: POST /v1/user with fake company_id.
        Assert: Response is 404 Not Found.
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
            "/v1/user/",
            headers=headers,
            json={
                "email": "newuser@example.com",
                "password": "NewPassword123!",
                "firstName": "New",
                "lastName": "User",
                "companyId": fake_company_id,
                "role": "BUYER",
            },
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_user_without_permission_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test non-admin cannot create user.

        Arrange: Create company and buyer user.
        Act: POST /v1/user with buyer auth.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        buyer = await UserFactory.create(
            db_session, company, role=UserRole.BUYER
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(buyer.id),
            role=UserRole.BUYER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/user/",
            headers=headers,
            json={
                "email": "newuser@example.com",
                "password": "NewPassword123!",
                "firstName": "New",
                "lastName": "User",
                "companyId": str(company.id),
                "role": "BUYER",
            },
        )

        # Assert
        assert response.status_code == 403


class TestPatchUser:
    """Tests for PATCH /v1/user/{user_id} endpoint."""

    @pytest.mark.asyncio
    async def test_patch_user_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test patch user updates specified fields.

        Arrange: Create company and user to patch.
        Act: PATCH /v1/user/{user_id} with new first_name.
        Assert: Response is 200 with updated user.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        user = await UserFactory.create(
            db_session,
            company,
            first_name="Original",
            last_name="Name",
            role=UserRole.ADMIN,  # needs UPDATE.USER permission
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(user.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.patch(
            f"/v1/user/{user.id}",
            headers=headers,
            json={"firstName": "Updated"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["firstName"] == "Updated"
        assert data["lastName"] == "Name"  # unchanged

    @pytest.mark.asyncio
    async def test_patch_user_email_to_existing_returns_409(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test patch user email to existing email returns 409.

        Arrange: Create company and two users.
        Act: PATCH first user's email to second user's email.
        Assert: Response is 409 Conflict.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        user1 = await UserFactory.create(
            db_session,
            company,
            email="user1@example.com",
            role=UserRole.ADMIN,
        )
        user2 = await UserFactory.create(
            db_session, company, email="user2@example.com"
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(user1.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.patch(
            f"/v1/user/{user1.id}",
            headers=headers,
            json={"email": "user2@example.com"},  # Duplicate
        )

        # Assert
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_patch_user_nonexistent_returns_404(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test patch non-existent user returns 404.

        Arrange: Create company and user for auth.
        Act: PATCH /v1/user/{fake_id}.
        Assert: Response is 404 Not Found.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        user = await UserFactory.create(
            db_session, company, role=UserRole.ADMIN
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(user.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        # Act
        response = await test_client.patch(
            f"/v1/user/{fake_uuid}",
            headers=headers,
            json={"firstName": "Updated"},
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_patch_user_different_company_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test patch user from different company returns 403.

        Arrange: Create two companies with users.
        Act: Admin from company1 tries to patch user from company2.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        company1 = await CompanyFactory.create(
            db_session, legal_name="Company One"
        )
        company2 = await CompanyFactory.create(
            db_session, legal_name="Company Two"
        )
        admin1 = await UserFactory.create_admin(db_session, company1)
        user2 = await UserFactory.create(db_session, company2)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin1.id),
            role=UserRole.ADMIN,
            company_id=str(company1.id),  # Different company
        )

        # Act
        response = await test_client.patch(
            f"/v1/user/{user2.id}",
            headers=headers,
            json={"firstName": "Hacked"},
        )

        # Assert
        assert response.status_code == 403


class TestDeleteUser:
    """Tests for DELETE /v1/user/{user_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_user_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test delete user returns deleted user.

        Arrange: Create company and user to delete.
        Act: DELETE /v1/user/{user_id}.
        Assert: Response is 200 with deleted user data.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, company)
        user_to_delete = await UserFactory.create(
            db_session, company, email="delete.me@example.com"
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.delete(
            f"/v1/user/{user_to_delete.id}", headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "delete.me@example.com"

    @pytest.mark.asyncio
    async def test_delete_user_nonexistent_returns_404(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test delete non-existent user returns 404.

        Arrange: Create company and admin.
        Act: DELETE /v1/user/{fake_id}.
        Assert: Response is 404 Not Found.
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
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        # Act
        response = await test_client.delete(
            f"/v1/user/{fake_uuid}", headers=headers
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_user_different_company_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test delete user from different company returns 403.

        Arrange: Create two companies with users.
        Act: Admin from company1 tries to delete user from company2.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        company1 = await CompanyFactory.create(
            db_session, legal_name="Company One"
        )
        company2 = await CompanyFactory.create(
            db_session, legal_name="Company Two"
        )
        admin1 = await UserFactory.create_admin(db_session, company1)
        user2 = await UserFactory.create(db_session, company2)
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin1.id),
            role=UserRole.ADMIN,
            company_id=str(company1.id),
        )

        # Act
        response = await test_client.delete(
            f"/v1/user/{user2.id}", headers=headers
        )

        # Assert
        assert response.status_code == 403


class TestSearchUsers:
    """Tests for POST /v1/user/search endpoint."""

    @pytest.mark.asyncio
    async def test_search_users_by_email(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test search users by email filter.

        Arrange: Create company and multiple users.
        Act: POST /v1/user/search with email filter.
        Assert: Response contains matching users.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(
            db_session, company, email="admin@example.com"
        )
        user1 = await UserFactory.create(
            db_session, company, email="john.doe@example.com"
        )
        user2 = await UserFactory.create(
            db_session, company, email="jane.doe@example.com"
        )
        user3 = await UserFactory.create(
            db_session, company, email="bob.smith@example.com"
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/user/search",
            headers=headers,
            json={"email": "doe"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        emails = [u["email"] for u in data]
        assert "john.doe@example.com" in emails
        assert "jane.doe@example.com" in emails
        assert "bob.smith@example.com" not in emails

    @pytest.mark.asyncio
    async def test_search_users_pagination(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test search users with pagination.

        Arrange: Create company and multiple users.
        Act: POST /v1/user/search with limit and offset.
        Assert: Response contains paginated results.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, company)
        # Create 5 additional users
        for i in range(5):
            await UserFactory.create(
                db_session, company, email=f"user{i}@example.com"
            )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        # Act - Get first 2 users
        response = await test_client.post(
            "/v1/user/search",
            headers=headers,
            json={"limit": 2, "offset": 0},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_search_users_by_role(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test search users by role filter.

        Arrange: Create company and users with different roles.
        Act: POST /v1/user/search with role filter.
        Assert: Response contains only users with matching role.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        admin = await UserFactory.create_admin(db_session, company)
        buyer = await UserFactory.create(
            db_session, company, role=UserRole.BUYER
        )
        seller = await UserFactory.create(
            db_session, company, role=UserRole.SELLER
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(admin.id),
            role=UserRole.ADMIN,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/user/search",
            headers=headers,
            json={"role": "BUYER"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        roles = [u["role"] for u in data]
        assert all(r == "BUYER" for r in roles)

    @pytest.mark.asyncio
    async def test_search_users_without_permission_returns_403(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test non-admin cannot search users.

        Arrange: Create company and buyer user.
        Act: POST /v1/user/search with buyer auth.
        Assert: Response is 403 Forbidden.
        """
        # Arrange
        company = await CompanyFactory.create(db_session)
        buyer = await UserFactory.create(
            db_session, company, role=UserRole.BUYER
        )
        await db_session.commit()

        headers = auth_headers(
            user_id=str(buyer.id),
            role=UserRole.BUYER,
            company_id=str(company.id),
        )

        # Act
        response = await test_client.post(
            "/v1/user/search",
            headers=headers,
            json={},
        )

        # Assert
        assert response.status_code == 403
