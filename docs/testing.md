# Testing Guidelines

This document outlines the testing conventions, structure, and requirements for all Moneta backend services.

## Table of Contents

- [Test Structure](#test-structure)
- [Naming Conventions](#naming-conventions)
- [Test Types](#test-types)
- [Writing Tests](#writing-tests)
- [Fixtures and Factories](#fixtures-and-factories)
- [Running Tests](#running-tests)
- [Service-Specific Notes](#service-specific-notes)
- [Checklist for New Tests](#checklist-for-new-tests)

---

## Test Structure

### Standard Directory Organization

Each service should follow this directory structure for tests:

```
<service_name>/tests/
├── __init__.py
├── conftest.py                    # Root configuration & shared fixtures
├── factories.py                   # Factory classes for test data generation
├── unit/                          # Unit tests (isolated functionality)
│   ├── __init__.py
│   └── <module>/
│       └── test_<function>.py
└── integration/                   # Integration tests (full workflows)
    ├── __init__.py
    ├── conftest.py                # Integration-specific fixtures
    └── <category>/
        └── test_<resource>.py
```

### Reference: Monolith Test Structure

```
monolith/tests/
├── __init__.py
├── conftest.py                    # Root configuration & shared fixtures
├── factories.py                   # Factory classes for test data generation
├── unit/                          # Unit tests (isolated functionality)
│   ├── __init__.py
│   └── utils/
│       ├── __init__.py
│       ├── filters/
│       │   ├── test_company_filters.py
│       │   ├── test_instrument_filters.py
│       │   └── test_user_filters.py
│       └── test_validations.py
└── integration/                   # Integration tests (full endpoint workflows)
    ├── __init__.py
    ├── conftest.py                # Integration-specific fixtures
    └── routers/
        ├── __init__.py
        ├── test_auth.py
        ├── test_company.py
        ├── test_company_address.py
        ├── test_instrument.py
        └── test_user.py
```

### File Separation by Resource/Endpoint

For services with API endpoints, each router/resource gets its own test file:

| Endpoint Pattern | Test File |
|------------------|-----------|
| `/v1/<resource>/*` | `test_<resource>.py` |

**Rule**: One test file per router/resource module. If a new router is added (e.g., `transaction.py`), create a corresponding `test_transaction.py`.

---

## Naming Conventions

### Test Files

| Type | Pattern | Example |
|------|---------|---------|
| All test files | `test_<module_name>.py` | `test_auth.py`, `test_validations.py` |

### Test Classes

| Type | Pattern | Example |
|------|---------|---------|
| Integration (per endpoint) | `Test<HttpMethod><Resource>` | `TestGetAllUsers`, `TestCreateCompany` |
| Unit tests | `Test<FunctionName>` | `TestBuildSortCompany`, `TestEnsureFuture` |

**Examples**:
```python
class TestGetAllCompanies:
    """Tests for GET /v1/company endpoint."""

class TestCreateUser:
    """Tests for POST /v1/user endpoint."""

class TestPatchUser:
    """Tests for PATCH /v1/user/{user_id} endpoint."""

class TestDeleteUser:
    """Tests for DELETE /v1/user/{user_id} endpoint."""

class TestSearchInstruments:
    """Tests for POST /v1/instrument/search endpoint."""
```

### Test Methods

| Scenario | Pattern | Example |
|----------|---------|---------|
| Success case | `test_<action>_success` | `test_login_success` |
| Error with status | `test_<action>_returns_<status>` | `test_login_invalid_email_returns_401` |
| Validation pass | `test_<condition>_passes` | `test_future_date_passes` |
| Validation fail | `test_<condition>_fails` | `test_past_date_fails` |
| Permission check | `test_<action>_without_permission_returns_403` | `test_create_user_without_permission_returns_403` |
| Not found | `test_<action>_nonexistent_returns_404` | `test_get_user_by_nonexistent_id_returns_404` |

**Key Principle**: Test names should clearly describe **what is being tested** and **what the expected outcome is**.

---

## Test Types

### Unit Tests

**Location**: `<service>/tests/unit/`

**Purpose**: Test isolated functions and utilities without external dependencies (database, network, etc.).

**When to Use**:
- Testing pure functions (filters, validators, utilities)
- Testing business logic that doesn't require database
- Testing data transformations

**Example**:
```python
class TestEnsureFuture:
    """Tests for the ensure_future validation function."""

    def test_future_date_passes(self, future_date):
        """
        Test that a future date passes validation.

        Arrange: Use a date 30 days in the future.
        Act: Call ensure_future with the date.
        Assert: No exception is raised.
        """
        # Should not raise
        ensure_future(future_date, "test_field")

    def test_past_date_fails(self, past_date):
        """
        Test that a past date fails validation.

        Arrange: Use a date 30 days in the past.
        Act: Call ensure_future with the date.
        Assert: IncorrectInputFormatException is raised.
        """
        with pytest.raises(IncorrectInputFormatException):
            ensure_future(past_date, "test_field")
```

### Integration Tests

**Location**: `<service>/tests/integration/`

**Purpose**: Test complete workflows including HTTP requests, database operations, and response validation.

**When to Use**:
- Testing API endpoints
- Testing database CRUD operations
- Testing authentication and authorization
- Testing complex business workflows
- Testing service-to-service communication

**Requirements**:
- Must use `@pytest.mark.asyncio` decorator (for async code)
- Must use async/await for all database and HTTP operations
- Must follow Arrange-Act-Assert pattern
- Must test both success and error scenarios

**Example**:
```python
@pytest.mark.asyncio
class TestCreateUser:
    """Tests for POST /v1/user endpoint."""

    async def test_create_user_success(
        self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
    ):
        """
        Test create user with valid data returns created user.

        Arrange: Create company and admin user for authentication.
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
        assert "id" in data
```

---

## Writing Tests

### Arrange-Act-Assert Pattern

All tests **must** follow the AAA pattern with explicit section comments:

```python
async def test_example(self, test_client: AsyncClient, db_session: AsyncSession):
    """
    Brief description of what the test validates.

    Arrange: What test data is created.
    Act: What action is performed.
    Assert: What results are expected.
    """
    # Arrange
    company = await CompanyFactory.create(db_session)
    user = await UserFactory.create(db_session, company)
    await db_session.commit()

    # Act
    response = await test_client.get(f"/v1/user/{user.id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == str(user.id)
```

### Docstring Format

Every test method **must** include a docstring with:

1. **Line 1**: Brief description of what the test validates
2. **Arrange**: Description of test data setup
3. **Act**: Description of the action being tested
4. **Assert**: Description of expected results

```python
async def test_login_inactive_account_returns_403(self, ...):
    """
    Test login with inactive account returns 403.

    Arrange: Create a company and an inactive user.
    Act: POST to /v1/auth/login with valid credentials.
    Assert: Response is 403 Forbidden with appropriate error message.
    """
```

### Test Coverage Requirements

For each endpoint/feature, tests **should** cover:

| Category | Required Tests |
|----------|---------------|
| **Success Cases** | At least one happy path test |
| **Authentication** | Test with valid/invalid/missing tokens |
| **Authorization** | Test with different roles/permissions |
| **Validation (422)** | Test missing required fields, invalid formats |
| **Not Found (404)** | Test with non-existent resource IDs |
| **Conflict (409)** | Test duplicate creation (if applicable) |
| **Business Logic** | Test state transitions, permissions, edge cases |

**Minimum Coverage per CRUD Endpoint**:

```python
class TestCreateResource:
    async def test_create_resource_success(...)
    async def test_create_resource_missing_required_field_returns_422(...)
    async def test_create_resource_without_permission_returns_403(...)
    async def test_create_resource_duplicate_returns_409(...)  # if applicable

class TestGetResource:
    async def test_get_resource_success(...)
    async def test_get_resource_not_found_returns_404(...)
    async def test_get_resource_without_permission_returns_403(...)

class TestUpdateResource:
    async def test_update_resource_success(...)
    async def test_update_resource_not_found_returns_404(...)
    async def test_update_resource_without_permission_returns_403(...)
    async def test_update_resource_different_company_returns_403(...)

class TestDeleteResource:
    async def test_delete_resource_success(...)
    async def test_delete_resource_not_found_returns_404(...)
    async def test_delete_resource_without_permission_returns_403(...)
```

---

## Fixtures and Factories

### Shared Fixtures Pattern

Each service should have a root `conftest.py` that provides common fixtures:

**Root `tests/conftest.py`** should provide:
- Common date/time fixtures
- Valid/invalid data samples
- Filter objects for testing

**Integration `tests/integration/conftest.py`** should provide:
- Database session with auto-cleanup
- HTTP test client
- Authentication helpers

### Reference: Monolith Fixtures

**Root `conftest.py`** provides:

| Fixture | Type | Description |
|---------|------|-------------|
| `future_date` | `date` | Date 30 days in the future |
| `past_date` | `date` | Date 30 days in the past |
| `valid_email` | `str` | Standard valid email format |
| `valid_password` | `str` | Standard valid password |
| `sample_*_filters` | Various | Pre-populated filter objects |
| `empty_*_filters` | Various | Empty filter objects |

**Integration `conftest.py`** provides:

| Fixture | Type | Description |
|---------|------|-------------|
| `db_session` | `AsyncSession` | Database session with auto-cleanup |
| `test_client` | `AsyncClient` | HTTP client with mocked JWT |
| `auth_headers` | `Callable` | Factory for creating auth headers |

### Using auth_headers (Monolith Pattern)

The `auth_headers` fixture is a factory function that creates JWT authorization headers:

```python
async def test_example(self, test_client, db_session, auth_headers):
    company = await CompanyFactory.create(db_session)
    user = await UserFactory.create_admin(db_session, company)
    await db_session.commit()

    # Create headers with specific claims
    headers = auth_headers(
        user_id=str(user.id),
        role=UserRole.ADMIN,
        company_id=str(company.id),
    )

    response = await test_client.get("/v1/user/", headers=headers)
```

### Factory Classes Pattern

Factories should be located in `tests/factories.py` and provide async methods for creating test data.

**Guidelines for Factories**:
1. Each entity type gets its own factory class
2. Provide a generic `create()` method with sensible defaults
3. Add convenience methods for common variants (e.g., `create_admin()`, `create_active()`)
4. Use `uuid4()` for unique identifiers
5. Always `flush()` and `refresh()` after creation

**Reference: Monolith Factories**:

```python
class CompanyFactory:
    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        legal_name: Optional[str] = None,
        trade_name: Optional[str] = None,
        registration_number: Optional[str] = None,
        incorporation_date: Optional[date] = None,
    ) -> Company:
        unique_suffix = uuid4().hex[:8]
        company = Company(
            id=uuid4(),
            legal_name=legal_name or f"Test Company {unique_suffix}",
            # ... other fields with defaults
        )
        session.add(company)
        await session.flush()
        await session.refresh(company)
        return company
```

```python
class UserFactory:
    @staticmethod
    async def create(session, company, *, email=None, role=UserRole.BUYER, ...):
        # Generic user creation

    @staticmethod
    async def create_admin(session, company, *, email=None, ...):
        # Convenience method for admin users

    @staticmethod
    async def create_inactive(session, company, *, email=None, ...):
        # Convenience method for inactive users
```

### Factory Best Practices

1. **Always commit after creating test data**:
   ```python
   company = await CompanyFactory.create(db_session)
   user = await UserFactory.create(db_session, company)
   await db_session.commit()  # Required!
   ```

2. **Use convenience methods when available**:
   ```python
   # Good
   admin = await UserFactory.create_admin(db_session, company)

   # Verbose (avoid unless you need custom values)
   admin = await UserFactory.create(
       db_session, company, role=UserRole.ADMIN
   )
   ```

3. **Override only what's necessary**:
   ```python
   # Good - only override what matters for this test
   user = await UserFactory.create(db_session, company, email="specific@test.com")

   # Bad - overriding everything unnecessarily
   user = await UserFactory.create(
       db_session, company,
       email="specific@test.com",
       first_name="Test",
       last_name="User",
       password="Password123!",
   )
   ```

---

## Running Tests

### Docker-Based Testing (Recommended)

For consistent test environments across all services:

```bash
# Run all tests for a specific service
docker-compose -f docker-compose.test.yml run --rm <service>-test pytest

# With verbose output
docker-compose -f docker-compose.test.yml run --rm <service>-test pytest -v

# Example: monolith
docker-compose -f docker-compose.test.yml run --rm monolith-test pytest -v
```

### Running Specific Tests

```bash
# Run a specific test file
pytest <service>/tests/integration/routers/test_company.py -v

# Run a specific test class
pytest <service>/tests/integration/routers/test_company.py::TestGetAllCompanies -v

# Run a specific test method
pytest <service>/tests/integration/routers/test_company.py::TestGetAllCompanies::test_get_all_companies_with_admin_permission -v

# Run tests matching a pattern
pytest -k "login" -v

# Run only unit tests
pytest <service>/tests/unit/ -v

# Run only integration tests
pytest <service>/tests/integration/ -v
```

### Test Output Options

```bash
# Show print statements and logs
pytest -v -s

# Show full traceback on failure
pytest -v --tb=long

# Stop on first failure
pytest -v -x

# Run last failed tests only
pytest -v --lf
```

### Using the Test Runner Script

A convenience script is available for running tests:

```bash
./scripts/run-tests.sh
```

---

## Service-Specific Notes

### monolith

The monolith is the reference implementation for all testing patterns. It includes:
- Comprehensive integration tests for all API endpoints
- Unit tests for utility functions and filters
- Complete factory implementations for all entities
- JWT authentication mocking via `auth_headers` fixture

**Test Database**: Uses a separate test database configured via `docker-compose.test.yml`.

### document_service

**Current State**: Unit tests only.

**Testing Recommendations**:
- Follow monolith patterns for integration tests
- Create factories for document-related entities
- Test file upload/download workflows
- Test document validation and processing

### scheduler_service

**Current State**: No tests implemented.

**Testing Recommendations**:
- Unit tests for job logic
- Integration tests for scheduled task execution
- Mock external service calls
- Test retry and failure scenarios

### zkp-service

**Current State**: No tests implemented.

**Testing Recommendations**:
- Unit tests for cryptographic functions
- Integration tests for proof generation/verification
- Test circuit compilation
- Test key management

---

## Checklist for New Tests

### Before Writing Tests

- [ ] Identify the service and resource to test
- [ ] Determine required test file location (`unit/` or `integration/`)
- [ ] Review existing test patterns in monolith
- [ ] Identify all scenarios to cover (success, errors, edge cases)
- [ ] Create/update factories if needed

### Writing Integration Tests

- [ ] Create test class with descriptive name (`Test<Method><Resource>`)
- [ ] Add class docstring describing the endpoint/feature being tested
- [ ] For each test method:
  - [ ] Use `@pytest.mark.asyncio` decorator (or class-level)
  - [ ] Write descriptive method name following naming conventions
  - [ ] Include docstring with Arrange/Act/Assert description
  - [ ] Follow AAA pattern with section comments
  - [ ] Assert status code first, then response body
  - [ ] Test all relevant response fields

### Test Coverage Checklist

For each new endpoint/feature, ensure you have tests for:

- [ ] **Success case** - Happy path with valid data
- [ ] **Authentication** - Missing or invalid token (401)
- [ ] **Authorization** - Insufficient permissions (403)
- [ ] **Validation** - Missing/invalid required fields (422)
- [ ] **Not Found** - Non-existent resource (404)
- [ ] **Conflict** - Duplicate creation if applicable (409)
- [ ] **Pagination** - If endpoint supports pagination
- [ ] **Filtering** - If endpoint supports filters
- [ ] **Edge cases** - Empty results, boundary values

### After Writing Tests

- [ ] Run tests locally to verify they pass
- [ ] Verify tests are isolated (can run independently)
- [ ] Check that cleanup happens properly (no test pollution)
- [ ] Review test output for deprecation warnings
- [ ] Update this documentation if new patterns are introduced

---

## Quick Reference

### Test Method Template

```python
@pytest.mark.asyncio
async def test_<action>_<expected_result>(
    self, test_client: AsyncClient, db_session: AsyncSession, auth_headers
):
    """
    Test <brief description>.

    Arrange: <setup description>.
    Act: <action description>.
    Assert: <expected result>.
    """
    # Arrange
    company = await CompanyFactory.create(db_session)
    user = await UserFactory.create_admin(db_session, company)
    await db_session.commit()

    headers = auth_headers(
        user_id=str(user.id),
        role=UserRole.ADMIN,
        company_id=str(company.id),
    )

    # Act
    response = await test_client.<method>(
        "<endpoint>",
        headers=headers,
        json={...},  # if POST/PATCH
    )

    # Assert
    assert response.status_code == <expected_status>
    data = response.json()
    assert data["<field>"] == <expected_value>
```

### Common Assertions

```python
# Status codes
assert response.status_code == 200  # Success
assert response.status_code == 401  # Unauthorized
assert response.status_code == 403  # Forbidden
assert response.status_code == 404  # Not Found
assert response.status_code == 409  # Conflict
assert response.status_code == 422  # Validation Error

# Response body
data = response.json()
assert data is not None
assert isinstance(data, list)
assert len(data) >= 1
assert "id" in data
assert data["email"] == "expected@email.com"

# List contents
emails = [u["email"] for u in data]
assert "expected@email.com" in emails

# Null checks
assert data.get("field") is None
assert response.json() is None
```

### Permission Matrix for Testing (Monolith Reference)

| Role | Typical Permissions |
|------|---------------------|
| `ADMIN` | Full access to company resources |
| `ISSUER` | Create/manage instruments |
| `BUYER` | View-only access |
| `SELLER` | View-only access |

Test different roles to ensure proper authorization:

```python
# Test admin access (should succeed)
headers = auth_headers(user_id=str(admin.id), role=UserRole.ADMIN, ...)
response = await test_client.post("/v1/user/", headers=headers, json={...})
assert response.status_code == 200

# Test buyer access (should fail)
headers = auth_headers(user_id=str(buyer.id), role=UserRole.BUYER, ...)
response = await test_client.post("/v1/user/", headers=headers, json={...})
assert response.status_code == 403
```

---

## Adding Tests to a New Service

When implementing tests for a service that doesn't have them yet:

1. **Create the test directory structure**:
   ```bash
   mkdir -p <service>/tests/unit
   mkdir -p <service>/tests/integration
   touch <service>/tests/__init__.py
   touch <service>/tests/conftest.py
   touch <service>/tests/factories.py
   touch <service>/tests/unit/__init__.py
   touch <service>/tests/integration/__init__.py
   touch <service>/tests/integration/conftest.py
   ```

2. **Copy and adapt conftest.py from monolith**:
   - Adjust database configuration for the service
   - Update imports for service-specific models
   - Modify authentication helpers if needed

3. **Create service-specific factories**:
   - Identify entities used by the service
   - Create factory classes following the monolith pattern
   - Add convenience methods for common test scenarios

4. **Add pytest configuration** (if not present):
   ```ini
   # pytest.ini
   [pytest]
   asyncio_mode = auto
   ```

5. **Update docker-compose.test.yml** (if needed):
   - Add test service configuration
   - Configure test database
   - Set up any required test dependencies
