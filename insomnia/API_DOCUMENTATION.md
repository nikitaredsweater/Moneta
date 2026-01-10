# Moneta API Documentation

This document provides comprehensive documentation for all Moneta API endpoints, including request/response formats, status codes, authentication requirements, and usage guidelines.

## Table of Contents

1. [General Information](#general-information)
2. [Authentication](#authentication)
3. [Auth Endpoints](#auth-endpoints)
4. [User Endpoints](#user-endpoints)
5. [Company Endpoints](#company-endpoints)
6. [Company Address Endpoints](#company-address-endpoints)
7. [Instrument Endpoints](#instrument-endpoints)
8. [Listing Endpoints](#listing-endpoints)
9. [Bid Endpoints](#bid-endpoints)
10. [Ask Endpoints](#ask-endpoints)

---

## General Information

### Base URL
```
http://localhost:8080/v1
```

### Request/Response Format
- All requests and responses use JSON format
- Request bodies should use **camelCase** field names
- Response bodies use **snake_case** field names
- Dates should be in ISO 8601 format (e.g., `2025-12-31`)
- Datetimes should be in ISO 8601 with timezone (e.g., `2025-12-31T23:59:59Z`)
- UUIDs should be in standard format (e.g., `550e8400-e29b-41d4-a716-446655440000`)

### Common Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid request format |
| 401 | Unauthorized - Invalid or missing authentication |
| 403 | Forbidden - Insufficient permissions or forbidden action |
| 404 | Not Found - Entity does not exist |
| 409 | Conflict - Entity with unique fields already exists |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error - Server-side error |

### Error Response Format
```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Authentication

### Bearer Token Authentication

Most endpoints require authentication via JWT Bearer token. Include the token in the `Authorization` header:

```
Authorization: Bearer <your_jwt_token>
```

### Token Lifetime
- Default expiration: **15 minutes** (900,000 milliseconds)
- Token type: `bearer`

### Obtaining a Token
Use the `/v1/auth/login` endpoint to obtain a JWT token.

---

## Auth Endpoints

### POST /v1/auth/login

**Description:** Authenticate a user and obtain a JWT access token.

**When to Use:** Call this endpoint when a user needs to log in to the system. The returned token should be stored and used for subsequent authenticated requests.

**Authentication Required:** No

**Permissions Required:** None

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | User's email address |
| `password` | string | Yes | User's password |

**Example Request:**
```json
{
  "email": "admin@example.com",
  "password": "password123"
}
```

#### Response

**Success (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires": 900000
}
```

| Field | Type | Description |
|-------|------|-------------|
| `access_token` | string | JWT token to use for authenticated requests |
| `token_type` | string | Always "bearer" |
| `expires` | integer | Token expiration time in milliseconds |

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 401 | User not found | `{"detail": "Invalid credentials"}` |
| 401 | Wrong password | `{"detail": "Invalid credentials"}` |
| 403 | Account not ACTIVE | `{"detail": "Wrong account status"}` |
| 422 | Missing required fields | Validation error details |

#### Notes
- Only users with `ACTIVE` account status can obtain tokens
- Users with `INACTIVE`, `PENDING`, `SUSPENDED`, `DISABLED`, or `DELETED` status cannot log in

---

## User Endpoints

### GET /v1/user/

**Description:** Retrieve all users in the system.

**When to Use:** Use when you need to fetch a complete list of all users without any filtering.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `VIEW.ALL_USERS`

#### Response

**Success (200 OK):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "company_id": "660e8400-e29b-41d4-a716-446655440001",
    "role": "BUYER",
    "account_status": "ACTIVE"
  }
]
```

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 401 | Missing/invalid token | `{"detail": "Not authenticated"}` |
| 403 | Insufficient permissions | `{"detail": "Insufficient permissions"}` |

---

### POST /v1/user/search

**Description:** Search for users with filtering, sorting, and pagination.

**When to Use:** Use when you need to find users matching specific criteria, or when implementing paginated user lists.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `VIEW.ALL_USERS`

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | No | Partial match on email (case-insensitive) |
| `firstName` | string | No | Partial match on first name (case-insensitive) |
| `lastName` | string | No | Partial match on last name (case-insensitive) |
| `role` | UserRole | No | Exact match on role |
| `companyId` | UUID | No | Exact match on company ID |
| `createdAtAfter` | date | No | Users created on or after this date |
| `createdAtBefore` | date | No | Users created on or before this date |
| `sort` | string | No | Sort order (default: `-createdAt`) |
| `limit` | integer | No | Results per page (default: 50, max: 200) |
| `offset` | integer | No | Pagination offset (default: 0) |

**UserRole Values:** `ADMIN`, `BUYER`, `SELLER`, `ISSUER`

**Example Request:**
```json
{
  "role": "BUYER",
  "companyId": "660e8400-e29b-41d4-a716-446655440001",
  "sort": "-createdAt,firstName",
  "limit": 20,
  "offset": 0
}
```

#### Response

**Success (200 OK):** Array of User objects (same format as GET /v1/user/)

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 401 | Missing/invalid token | `{"detail": "Not authenticated"}` |
| 403 | Insufficient permissions | `{"detail": "Insufficient permissions"}` |
| 422 | Invalid filter values | Validation error details |

---

### GET /v1/user/{user_id}

**Description:** Retrieve a specific user by their ID.

**When to Use:** Use when you need to fetch details for a specific user.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `VIEW.USER`

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | UUID | The unique identifier of the user |

#### Response

**Success (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "company_id": "660e8400-e29b-41d4-a716-446655440001",
  "role": "BUYER",
  "account_status": "ACTIVE"
}
```

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 401 | Missing/invalid token | `{"detail": "Not authenticated"}` |
| 403 | Insufficient permissions | `{"detail": "Insufficient permissions"}` |
| 404 | User not found | `{"detail": "Entity was not found"}` |

---

### POST /v1/user/

**Description:** Create a new user.

**When to Use:** Use when onboarding a new user to the system.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `CREATE.USER`

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | User's email address (must be unique) |
| `firstName` | string | Yes | User's first name |
| `lastName` | string | Yes | User's last name |
| `password` | string | Yes | User's password |
| `companyId` | UUID | Yes | ID of the company the user belongs to |
| `role` | UserRole | Yes | User's role in the system |

**Example Request:**
```json
{
  "email": "newuser@example.com",
  "firstName": "Jane",
  "lastName": "Smith",
  "password": "SecurePassword123!",
  "companyId": "660e8400-e29b-41d4-a716-446655440001",
  "role": "BUYER"
}
```

#### Response

**Success (201 Created):** User object with generated ID and timestamps

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 401 | Missing/invalid token | `{"detail": "Not authenticated"}` |
| 403 | Insufficient permissions | `{"detail": "Insufficient permissions"}` |
| 404 | Company not found | `{"detail": "Entity was not found"}` |
| 409 | Email already exists | `{"detail": "Entity with such unique fields already exists"}` |
| 422 | Validation error | Validation error details |
| 500 | Creation failed | `{"detail": "Failed to save the entity"}` |

---

### PATCH /v1/user/{user_id}

**Description:** Update an existing user's information.

**When to Use:** Use when modifying user details such as name, email, role, or account status.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `UPDATE.USER` + same company as target user

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | UUID | The unique identifier of the user to update |

#### Request Body

All fields are optional. Only include fields you want to update.

| Field | Type | Description |
|-------|------|-------------|
| `email` | string | New email address |
| `firstName` | string | New first name |
| `lastName` | string | New last name |
| `accountStatus` | ActivationStatus | New account status |
| `role` | UserRole | New role |

**ActivationStatus Values:** `ACTIVE`, `INACTIVE`, `PENDING`, `SUSPENDED`, `DISABLED`, `DELETED`

**Example Request:**
```json
{
  "firstName": "Janet",
  "accountStatus": "SUSPENDED"
}
```

#### Response

**Success (200 OK):** Updated User object

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 401 | Missing/invalid token | `{"detail": "Not authenticated"}` |
| 403 | Insufficient permissions | `{"detail": "Insufficient permissions"}` |
| 403 | Different company | `{"detail": "Forbidden Action"}` |
| 404 | User not found | `{"detail": "Entity was not found"}` |
| 409 | Email already exists | `{"detail": "Entity with such unique fields already exists"}` |
| 422 | Empty name fields | `{"detail": "Entity passed in has an invalid field"}` |

---

### DELETE /v1/user/{user_id}

**Description:** Delete a user from the system.

**When to Use:** Use when removing a user from the system. This performs a soft delete.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `DELETE.USER` + same company as target user

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | UUID | The unique identifier of the user to delete |

#### Response

**Success (200 OK):** The deleted User object

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 401 | Missing/invalid token | `{"detail": "Not authenticated"}` |
| 403 | Insufficient permissions | `{"detail": "Insufficient permissions"}` |
| 403 | Different company | `{"detail": "Forbidden Action"}` |
| 404 | User not found | `{"detail": "Entity was not found"}` |

---

## Company Endpoints

### GET /v1/company/

**Description:** Retrieve all companies in the system.

**When to Use:** Use when you need a complete list of all registered companies.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `VIEW.COMPANY`

#### Response

**Success (200 OK):**
```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z",
    "legal_name": "Acme Corporation",
    "trade_name": "Acme",
    "registration_number": "12345678",
    "incorporation_date": "2020-01-15"
  }
]
```

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 401 | Missing/invalid token | `{"detail": "Not authenticated"}` |
| 403 | Insufficient permissions | `{"detail": "Insufficient permissions"}` |

---

### GET /v1/company/{company_id}

**Description:** Retrieve a specific company by ID with optional related entities.

**When to Use:** Use when fetching company details. Add `?include=` parameter to fetch related entities in a single request.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `VIEW.COMPANY`

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `company_id` | UUID | The unique identifier of the company |

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `include` | string | Comma-separated list of relations to include |

**Include Options:** `addresses`, `users`, `instruments`

**Example:** `/v1/company/{id}?include=addresses,users`

#### Response

**Success (200 OK):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z",
  "legal_name": "Acme Corporation",
  "trade_name": "Acme",
  "registration_number": "12345678",
  "incorporation_date": "2020-01-15",
  "addresses": [...],
  "users": [...],
  "instruments": [...]
}
```

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 401 | Missing/invalid token | `{"detail": "Not authenticated"}` |
| 403 | Insufficient permissions | `{"detail": "Insufficient permissions"}` |
| 404 | Company not found | `{"detail": "Entity was not found"}` |

---

### POST /v1/company/search

**Description:** Search for companies with filtering, sorting, and pagination.

**When to Use:** Use when searching for companies matching specific criteria.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `VIEW.COMPANY`

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `legalName` | string | No | Partial match on legal name |
| `tradeName` | string | No | Partial match on trade name |
| `registrationNumber` | string | No | Partial match on registration number |
| `incorporationDateAfter` | date | No | Companies incorporated on or after |
| `incorporationDateBefore` | date | No | Companies incorporated on or before |
| `createdAtAfter` | date | No | Companies created on or after |
| `createdAtBefore` | date | No | Companies created on or before |
| `sort` | string | No | Sort order (default: `-createdAt`) |
| `limit` | integer | No | Results per page (default: 50, max: 200) |
| `offset` | integer | No | Pagination offset (default: 0) |

**Example Request:**
```json
{
  "legalName": "Acme",
  "incorporationDateAfter": "2020-01-01",
  "limit": 10
}
```

#### Response

**Success (200 OK):** Array of Company objects

---

### POST /v1/company/

**Description:** Create a new company.

**When to Use:** Use when registering a new company in the system.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `CREATE.COMPANY`

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `legalName` | string | Yes | Company's legal name |
| `tradeName` | string | No | Company's trade/brand name |
| `registrationNumber` | string | Yes | Company registration number |
| `incorporationDate` | date | Yes | Date of incorporation |

**Example Request:**
```json
{
  "legalName": "New Company LLC",
  "tradeName": "NewCo",
  "registrationNumber": "87654321",
  "incorporationDate": "2025-01-01"
}
```

#### Response

**Success (201 Created):** Company object with generated ID

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 401 | Missing/invalid token | `{"detail": "Not authenticated"}` |
| 403 | Insufficient permissions | `{"detail": "Insufficient permissions"}` |
| 422 | Validation error | Validation error details |

---

## Company Address Endpoints

### GET /v1/company-address/

**Description:** Retrieve all company addresses in the system.

**When to Use:** Use when you need a complete list of all company addresses.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `VIEW.COMPANY_ADDRESS`

#### Response

**Success (200 OK):**
```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z",
    "type": "REGISTERED",
    "street": "123 Main Street",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "US",
    "company_id": "660e8400-e29b-41d4-a716-446655440001"
  }
]
```

---

### POST /v1/company-address/

**Description:** Create a new company address.

**When to Use:** Use when adding an address to a company's profile.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `CREATE.COMPANY_ADDRESS`

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | AddressType | Yes | Type of address |
| `street` | string | Yes | Street address |
| `city` | string | Yes | City name |
| `state` | string | No | State/province |
| `postalCode` | string | Yes | Postal/ZIP code |
| `country` | string | Yes | ISO 3166-1 alpha-2 country code |
| `companyId` | UUID | Yes | ID of the company |

**AddressType Values:** `REGISTERED`, `BILLING`, `OFFICE`, `SHIPPING`, `OTHER`

**Example Request:**
```json
{
  "type": "REGISTERED",
  "street": "123 Main Street",
  "city": "New York",
  "state": "NY",
  "postalCode": "10001",
  "country": "US",
  "companyId": "660e8400-e29b-41d4-a716-446655440001"
}
```

#### Response

**Success (201 Created):** CompanyAddress object with generated ID

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 401 | Missing/invalid token | `{"detail": "Not authenticated"}` |
| 403 | Insufficient permissions | `{"detail": "Insufficient permissions"}` |
| 404 | Company not found | `{"detail": "Entity was not found"}` |
| 422 | Validation error | Validation error details |

---

## Instrument Endpoints

### POST /v1/instrument/search

**Description:** Search for instruments with filtering, sorting, and pagination.

**When to Use:** Use when searching for financial instruments matching specific criteria.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `VIEW.INSTRUMENT`

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `minFaceValue` | float | No | Minimum face value |
| `maxFaceValue` | float | No | Maximum face value |
| `currency` | string | No | ISO 4217 currency code (3 chars) |
| `maturityDateAfter` | date | No | Instruments maturing after |
| `maturityDateBefore` | date | No | Instruments maturing before |
| `createdAtAfter` | date | No | Created after this date |
| `createdAtBefore` | date | No | Created before this date |
| `minMaturityPayment` | float | No | Minimum maturity payment |
| `maxMaturityPayment` | float | No | Maximum maturity payment |
| `instrumentStatus` | InstrumentStatus | No | Filter by instrument status |
| `maturityStatus` | MaturityStatus | No | Filter by maturity status |
| `tradingStatus` | TradingStatus | No | Filter by trading status |
| `issuerId` | UUID[] | No | Filter by issuer company IDs |
| `createdBy` | UUID[] | No | Filter by creator user IDs |
| `sort` | string | No | Sort order (default: `-createdAt`) |
| `limit` | integer | No | Results per page (default: 50, max: 200) |
| `offset` | integer | No | Pagination offset (default: 0) |

**InstrumentStatus Values:** `DRAFT`, `PENDING_APPROVAL`, `ACTIVE`, `MATURED`, `REJECTED`

**MaturityStatus Values:** `NOT_DUE`, `DUE`, `SETTLED`, `DEFAULTED`

**TradingStatus Values:** `DRAFT`, `OPEN`, `HALTED`, `CLOSED`

**Example Request:**
```json
{
  "instrumentStatus": "ACTIVE",
  "currency": "USD",
  "minFaceValue": 10000,
  "limit": 20
}
```

#### Response

**Success (200 OK):**
```json
[
  {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z",
    "name": "Corporate Bond 2025",
    "face_value": 100000.00,
    "currency": "USD",
    "maturity_date": "2026-01-15",
    "maturity_payment": 105000.00,
    "instrument_status": "ACTIVE",
    "maturity_status": "DUE",
    "trading_status": "OPEN",
    "issuer_id": "660e8400-e29b-41d4-a716-446655440001",
    "created_by": "550e8400-e29b-41d4-a716-446655440000",
    "public_payload": {...}
  }
]
```

---

### GET /v1/instrument/{instrument_id}

**Description:** Retrieve a specific instrument by ID with optional related documents.

**When to Use:** Use when fetching instrument details. Add `?include=documents` to include associated documents.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `VIEW.INSTRUMENT`

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `instrument_id` | UUID | The unique identifier of the instrument |

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `include` | string | Set to `documents` to include associated documents |

#### Response

**Success (200 OK):** Instrument object with optional `instrument_documents` array

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 404 | Instrument not found | `{"detail": "Instrument with ID {id} does not exist"}` |

---

### POST /v1/instrument/

**Description:** Create a new financial instrument.

**When to Use:** Use when an issuer wants to create a new instrument. The instrument starts in DRAFT status.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `CREATE.INSTRUMENT`

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Instrument name (max 255 chars) |
| `faceValue` | float | Yes | Face value of the instrument |
| `currency` | string | Yes | ISO 4217 currency code (3 chars) |
| `maturityDate` | date | Yes | Date when instrument matures |
| `maturityPayment` | float | Yes | Payment amount at maturity |
| `publicPayload` | object | No | Additional public metadata |

**Example Request:**
```json
{
  "name": "Corporate Bond 2025",
  "faceValue": 100000.00,
  "currency": "USD",
  "maturityDate": "2026-01-15",
  "maturityPayment": 105000.00,
  "publicPayload": {
    "description": "5% annual yield corporate bond"
  }
}
```

#### Response

**Success (201 Created):** Instrument object with:
- `instrument_status`: `DRAFT`
- `maturity_status`: `NOT_DUE`
- `trading_status`: `DRAFT`
- `issuer_id`: Current user's company ID
- `created_by`: Current user's ID

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 401 | Missing/invalid token | `{"detail": "Not authenticated"}` |
| 403 | Insufficient permissions | `{"detail": "Insufficient permissions"}` |
| 422 | Validation error | Validation error details |
| 500 | Creation failed | `{"detail": "Failed to save the entity"}` |

---

### PATCH /v1/instrument/{instrument_id}

**Description:** Update a draft instrument.

**When to Use:** Use when modifying an instrument that is still in DRAFT status. Only the issuing company can update their instruments.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `UPDATE.INSTRUMENT` + must be from issuer company + instrument must be DRAFT

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `instrument_id` | UUID | The unique identifier of the instrument |

#### Request Body

At least one field must be provided.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | New instrument name |
| `faceValue` | float | New face value (must be > 0) |
| `currency` | string | New currency code |
| `maturityDate` | date | New maturity date (must be in future) |
| `maturityPayment` | float | New maturity payment (must be > 0) |
| `publicPayload` | object | New public metadata |

**Example Request:**
```json
{
  "faceValue": 150000.00,
  "maturityPayment": 157500.00
}
```

#### Response

**Success (200 OK):** Updated Instrument object

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 403 | Not DRAFT status | `{"detail": "This instrument cannot be updated"}` |
| 403 | Different company | `{"detail": "This instrument does not belong to you"}` |
| 404 | Not found | `{"detail": "Instrument with ID {id} does not exist"}` |
| 422 | No fields provided | `{"detail": "At least one field must be provided"}` |

---

### POST /v1/instrument/{instrument_id}/transition

**Description:** Transition an instrument to a new status.

**When to Use:** Use when changing the workflow status of an instrument (e.g., submitting for approval, approving, rejecting).

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `UPDATE.INSTRUMENT` + role-based transition rules

#### Allowed Transitions

| Current Status | New Status | Allowed Roles |
|----------------|------------|---------------|
| DRAFT | PENDING_APPROVAL | ISSUER, ADMIN |
| PENDING_APPROVAL | ACTIVE | ADMIN |
| PENDING_APPROVAL | REJECTED | ADMIN |

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `instrument_id` | UUID | The unique identifier of the instrument |

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `newStatus` | InstrumentStatus | Yes | Target status |

**Example Request:**
```json
{
  "newStatus": "PENDING_APPROVAL"
}
```

#### Response

**Success (200 OK):** Updated Instrument object

**Side Effects when transitioning to ACTIVE:**
- `maturity_status` is set to `DUE`
- Initial ownership is recorded (issuer becomes owner)

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 403 | Invalid transition | `{"detail": "You cannot perform this transition"}` |
| 404 | Not found | `{"detail": "Instrument with ID {id} does not exist"}` |

---

### POST /v1/instrument/{instrument_id}/documents/{document_id}

**Description:** Associate a document with an instrument.

**When to Use:** Use when attaching supporting documents (e.g., prospectus, terms) to an instrument.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `UPDATE.INSTRUMENT`

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `instrument_id` | UUID | The instrument ID |
| `document_id` | UUID | The document ID to associate |

#### Response

**Success (200 OK):**
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440004",
  "instrument_id": "880e8400-e29b-41d4-a716-446655440003",
  "document_id": "aa0e8400-e29b-41d4-a716-446655440005"
}
```

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 404 | Instrument not found | `{"detail": "Instrument with ID {id} does not exist"}` |
| 404 | Document not found | `{"detail": "Document with ID {id} does not exist"}` |
| 409 | Already associated | `{"detail": "This document is already associated with this instrument"}` |
| 500 | Creation failed | `{"detail": "Failed to associate document with instrument"}` |

---

## Listing Endpoints

### POST /v1/listing/search

**Description:** Search for listings with filtering, sorting, and pagination.

**When to Use:** Use when searching for instrument listings on the marketplace.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `VIEW.INSTRUMENT`

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `include` | string | Set to `instrument` to include related instrument |

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `instrumentId` | UUID[] | No | Filter by instrument IDs |
| `sellerCompanyId` | UUID[] | No | Filter by seller company IDs |
| `listingCreatorUserId` | UUID[] | No | Filter by creator user IDs |
| `status` | ListingStatus | No | Filter by listing status |
| `sort` | string | No | Sort order (default: `-createdAt`) |
| `limit` | integer | No | Results per page (default: 50, max: 200) |
| `offset` | integer | No | Pagination offset (default: 0) |

**ListingStatus Values:** `OPEN`, `WITHDRAWN`, `SUSPENDED`, `CLOSED`

**Example Request:**
```json
{
  "status": "OPEN",
  "limit": 20
}
```

#### Response

**Success (200 OK):**
```json
[
  {
    "id": "bb0e8400-e29b-41d4-a716-446655440006",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z",
    "instrument_id": "880e8400-e29b-41d4-a716-446655440003",
    "seller_company_id": "660e8400-e29b-41d4-a716-446655440001",
    "listing_creator_user_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "OPEN",
    "instrument": null
  }
]
```

---

### GET /v1/listing/{listing_id}

**Description:** Retrieve a specific listing by ID.

**When to Use:** Use when fetching listing details. Add `?include=instrument` to include the related instrument.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `VIEW.INSTRUMENT`

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `listing_id` | UUID | The unique identifier of the listing |

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `include` | string | Set to `instrument` to include related instrument |

#### Response

**Success (200 OK):** Listing object with optional `instrument` field

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 404 | Listing not found | `{"detail": "Listing with ID {id} does not exist"}` |

---

### POST /v1/listing/

**Description:** Create a new listing for an instrument.

**When to Use:** Use when a company wants to list their instrument for sale on the marketplace.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `UPDATE.INSTRUMENT` + must own the instrument + no existing OPEN listing

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `instrumentId` | UUID | Yes | ID of the instrument to list |

**Example Request:**
```json
{
  "instrumentId": "880e8400-e29b-41d4-a716-446655440003"
}
```

#### Response

**Success (201 Created):** Listing object with:
- `status`: `OPEN`
- `seller_company_id`: Current user's company ID
- `listing_creator_user_id`: Current user's ID

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 403 | No active ownership | `{"detail": "This instrument has no active owner"}` |
| 403 | Not the owner | `{"detail": "Your company does not own this instrument"}` |
| 404 | Instrument not found | `{"detail": "Instrument with ID {id} does not exist"}` |
| 409 | Open listing exists | `{"detail": "An open listing already exists for this instrument"}` |
| 500 | Creation failed | `{"detail": "Failed to create listing"}` |

---

### POST /v1/listing/{listing_id}/transition

**Description:** Transition a listing to a new status.

**When to Use:** Use when withdrawing, suspending, or closing a listing.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `UPDATE.INSTRUMENT` + role-based rules

#### Allowed Transitions

| Current Status | New Status | Who Can Do It |
|----------------|------------|---------------|
| OPEN | WITHDRAWN | Seller company only |
| OPEN | SUSPENDED | Admin only |
| OPEN | CLOSED | Admin only |
| SUSPENDED | OPEN | Admin only |
| WITHDRAWN | SUSPENDED | Admin only |

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `listing_id` | UUID | The unique identifier of the listing |

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | ListingStatus | Yes | Target status |

**Example Request:**
```json
{
  "status": "WITHDRAWN"
}
```

#### Response

**Success (200 OK):** Updated Listing object

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 403 | Invalid transition for role | `{"detail": "Admin cannot transition from {status} to {status}"}` |
| 403 | Invalid transition | `{"detail": "Cannot transition from {status} to {status}"}` |
| 403 | Not seller company | `{"detail": "You do not have permission to update this listing"}` |
| 404 | Listing not found | `{"detail": "Listing with ID {id} does not exist"}` |

---

## Bid Endpoints

### POST /v1/bid/search

**Description:** Search for bids with filtering, sorting, and pagination.

**When to Use:** Use when searching for bids on listings.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `VIEW.INSTRUMENT`

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `include` | string | Set to `listing` to include related listing |

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `listingId` | UUID[] | No | Filter by listing IDs |
| `bidderCompanyId` | UUID[] | No | Filter by bidder company IDs |
| `bidderUserId` | UUID[] | No | Filter by bidder user IDs |
| `status` | BidStatus | No | Filter by bid status |
| `minAmount` | float | No | Minimum bid amount |
| `maxAmount` | float | No | Maximum bid amount |
| `currency` | string | No | Filter by currency (ISO 4217) |
| `sort` | string | No | Sort order (default: `-createdAt`) |
| `limit` | integer | No | Results per page (default: 50, max: 200) |
| `offset` | integer | No | Pagination offset (default: 0) |

**BidStatus Values:** `PENDING`, `WITHDRAWN`, `SUSPENDED`, `SELECTED`, `NOT_SELECTED`

**Example Request:**
```json
{
  "listingId": ["bb0e8400-e29b-41d4-a716-446655440006"],
  "status": "PENDING"
}
```

#### Response

**Success (200 OK):**
```json
[
  {
    "id": "cc0e8400-e29b-41d4-a716-446655440007",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z",
    "listing_id": "bb0e8400-e29b-41d4-a716-446655440006",
    "bidder_company_id": "dd0e8400-e29b-41d4-a716-446655440008",
    "bidder_user_id": "ee0e8400-e29b-41d4-a716-446655440009",
    "amount": 95000.00,
    "currency": "USD",
    "valid_until": "2025-12-31T23:59:59Z",
    "status": "PENDING",
    "listing": null
  }
]
```

---

### GET /v1/bid/{bid_id}

**Description:** Retrieve a specific bid by ID.

**When to Use:** Use when fetching bid details. Add `?include=listing` to include the related listing.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `VIEW.INSTRUMENT`

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `bid_id` | UUID | The unique identifier of the bid |

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `include` | string | Set to `listing` to include related listing |

#### Response

**Success (200 OK):** Bid object with optional `listing` field

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 404 | Bid not found | `{"detail": "Bid with ID {id} does not exist"}` |

---

### POST /v1/bid/

**Description:** Create a new bid on a listing.

**When to Use:** Use when a company wants to place a bid on an instrument listing.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `UPDATE.INSTRUMENT` + cannot self-bid + listing must be OPEN

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `listingId` | UUID | Yes | ID of the listing to bid on |
| `amount` | float | Yes | Bid amount (must be > 0) |
| `currency` | string | Yes | ISO 4217 currency code (3 chars) |
| `validUntil` | datetime | No | Bid expiration timestamp |

**Example Request:**
```json
{
  "listingId": "bb0e8400-e29b-41d4-a716-446655440006",
  "amount": 95000.00,
  "currency": "USD",
  "validUntil": "2025-12-31T23:59:59Z"
}
```

#### Response

**Success (201 Created):** Bid object with:
- `status`: `PENDING`
- `bidder_company_id`: Current user's company ID
- `bidder_user_id`: Current user's ID

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 403 | Listing not OPEN | `{"detail": "Listing is not open for bidding (status: {status})"}` |
| 403 | Self-bidding | `{"detail": "You cannot bid on your own listing"}` |
| 404 | Listing not found | `{"detail": "Listing with ID {id} does not exist"}` |
| 422 | Invalid amount | Validation error (amount must be > 0) |
| 422 | Invalid currency | Validation error (must be 3 chars) |
| 500 | Creation failed | `{"detail": "Failed to create bid"}` |

---

### POST /v1/bid/{bid_id}/transition

**Description:** Transition a bid to a new status.

**When to Use:** Use when withdrawing or suspending a bid.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `UPDATE.INSTRUMENT` + role-based rules

#### Allowed Transitions

| Current Status | New Status | Who Can Do It |
|----------------|------------|---------------|
| PENDING | WITHDRAWN | Bidder company only |
| PENDING | SUSPENDED | Admin only |
| WITHDRAWN | SUSPENDED | Admin only |

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `bid_id` | UUID | The unique identifier of the bid |

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | BidStatus | Yes | Target status |

**Example Request:**
```json
{
  "status": "WITHDRAWN"
}
```

#### Response

**Success (200 OK):** Updated Bid object

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 403 | Invalid transition | `{"detail": "Cannot transition from {status} to {status}"}` |
| 403 | Listing not OPEN | `{"detail": "Listing is not open"}` |
| 404 | Bid not found | `{"detail": "Bid with ID {id} does not exist"}` |

---

### POST /v1/bid/{bid_id}/accept

**Description:** Accept a bid on a listing.

**When to Use:** Use when the listing owner wants to accept a specific bid. This marks the bid as SELECTED and all other PENDING bids as NOT_SELECTED.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `UPDATE.INSTRUMENT` + must be seller company + listing must be OPEN + bid must be PENDING

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `bid_id` | UUID | The unique identifier of the bid to accept |

#### Response

**Success (200 OK):** Updated Bid object with `status`: `SELECTED`

**Side Effects:**
- All other PENDING bids on the same listing are set to `NOT_SELECTED`

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 403 | Not seller company | `{"detail": "You are not the owner of this listing"}` |
| 403 | Listing not OPEN | `{"detail": "Listing is not open"}` |
| 403 | Bid not PENDING | `{"detail": "Bid is not in PENDING status"}` |
| 404 | Bid not found | `{"detail": "Bid with ID {id} does not exist"}` |

---

### POST /v1/bid/{bid_id}/reject

**Description:** Reject a bid on a listing.

**When to Use:** Use when the listing owner wants to reject a specific bid.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `UPDATE.INSTRUMENT` + must be seller company + listing must be OPEN + bid must be PENDING

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `bid_id` | UUID | The unique identifier of the bid to reject |

#### Response

**Success (200 OK):** Updated Bid object with `status`: `NOT_SELECTED`

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 403 | Not seller company | `{"detail": "You are not the owner of this listing"}` |
| 403 | Listing not OPEN | `{"detail": "Listing is not open"}` |
| 403 | Bid not PENDING | `{"detail": "Bid is not in PENDING status"}` |
| 404 | Bid not found | `{"detail": "Bid with ID {id} does not exist"}` |

---

## Ask Endpoints

### POST /v1/ask/search

**Description:** Search for asks with filtering, sorting, and pagination.

**When to Use:** Use when searching for asking prices on listings.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `VIEW.INSTRUMENT`

**Visibility Rules:**
- Non-owners can only see `ACTIVE` asks
- Listing owners and ADMINs can see all asks for their listings

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `include` | string | Set to `listing` to include related listing |

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `listingId` | UUID[] | No | Filter by listing IDs |
| `askerCompanyId` | UUID[] | No | Filter by asker company IDs |
| `askerUserId` | UUID[] | No | Filter by asker user IDs |
| `status` | AskStatus | No | Filter by ask status |
| `minAmount` | float | No | Minimum ask amount |
| `maxAmount` | float | No | Maximum ask amount |
| `currency` | string | No | Filter by currency (ISO 4217) |
| `executionMode` | ExecutionMode | No | Filter by execution mode |
| `binding` | boolean | No | Filter by binding status |
| `sort` | string | No | Sort order (default: `-createdAt`) |
| `limit` | integer | No | Results per page (default: 50, max: 200) |
| `offset` | integer | No | Pagination offset (default: 0) |

**AskStatus Values:** `ACTIVE`, `WITHDRAWN`, `SUSPENDED`

**ExecutionMode Values:** `AUTO`, `MANUAL`

**Example Request:**
```json
{
  "listingId": ["bb0e8400-e29b-41d4-a716-446655440006"],
  "executionMode": "AUTO"
}
```

#### Response

**Success (200 OK):**
```json
[
  {
    "id": "ff0e8400-e29b-41d4-a716-44665544000a",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z",
    "listing_id": "bb0e8400-e29b-41d4-a716-446655440006",
    "asker_company_id": "660e8400-e29b-41d4-a716-446655440001",
    "asker_user_id": "550e8400-e29b-41d4-a716-446655440000",
    "amount": 100000.00,
    "currency": "USD",
    "valid_until": "2025-12-31T23:59:59Z",
    "execution_mode": "MANUAL",
    "binding": false,
    "status": "ACTIVE",
    "listing": null
  }
]
```

---

### GET /v1/ask/{ask_id}

**Description:** Retrieve a specific ask by ID.

**When to Use:** Use when fetching ask details. Add `?include=listing` to include the related listing.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `VIEW.INSTRUMENT`

**Visibility Rules:**
- Non-owners can only view `ACTIVE` asks
- Listing owners and ADMINs can view all asks

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ask_id` | UUID | The unique identifier of the ask |

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `include` | string | Set to `listing` to include related listing |

#### Response

**Success (200 OK):** Ask object with optional `listing` field

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 404 | Ask not found or not visible | `{"detail": "Ask with ID {id} does not exist"}` |

---

### POST /v1/ask/

**Description:** Create a new ask on a listing.

**When to Use:** Use when a seller wants to set an asking price for their listing.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `UPDATE.INSTRUMENT` + must be seller company + listing must be OPEN

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `listingId` | UUID | Yes | ID of the listing |
| `amount` | float | Yes | Asking amount (must be > 0) |
| `currency` | string | Yes | ISO 4217 currency code (3 chars) |
| `validUntil` | datetime | No | Ask expiration timestamp (must be in future) |
| `executionMode` | ExecutionMode | No | Execution mode (default: `MANUAL`) |
| `binding` | boolean | No | Whether ask is binding (default: `false`) |

**ExecutionMode Values:**
- `MANUAL` - Bids require manual review and acceptance
- `AUTO` - Bids matching the ask price are automatically accepted

**Example Request:**
```json
{
  "listingId": "bb0e8400-e29b-41d4-a716-446655440006",
  "amount": 100000.00,
  "currency": "USD",
  "validUntil": "2025-12-31T23:59:59Z",
  "executionMode": "AUTO",
  "binding": true
}
```

#### Response

**Success (201 Created):** Ask object with:
- `status`: `ACTIVE`
- `asker_company_id`: Current user's company ID
- `asker_user_id`: Current user's ID

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 403 | Listing not OPEN | `{"detail": "Listing is not open (status: {status})"}` |
| 403 | Not seller company | `{"detail": "Only the listing owner can create asks"}` |
| 403 | Invalid amount | `{"detail": "Amount must be greater than zero"}` |
| 403 | Invalid validUntil | `{"detail": "valid_until must be in the future"}` |
| 404 | Listing not found | `{"detail": "Listing with ID {id} does not exist"}` |
| 422 | Validation error | Validation error details |
| 500 | Creation failed | `{"detail": "Failed to create ask"}` |

---

### PATCH /v1/ask/{ask_id}

**Description:** Update an existing ask's price or validity.

**When to Use:** Use when the seller wants to modify their asking price or extend/shorten the validity period.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `UPDATE.INSTRUMENT` + must be asker company + ask must be ACTIVE + listing must be OPEN

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ask_id` | UUID | The unique identifier of the ask |

#### Request Body

All fields are optional. Only include fields you want to update.

| Field | Type | Description |
|-------|------|-------------|
| `amount` | float | New asking amount (must be > 0) |
| `currency` | string | New currency code |
| `validUntil` | datetime | New expiration timestamp |

**Example Request:**
```json
{
  "amount": 95000.00,
  "validUntil": "2026-01-31T23:59:59Z"
}
```

#### Response

**Success (200 OK):** Updated Ask object

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 403 | Ask not ACTIVE | `{"detail": "Ask is not active"}` |
| 403 | Listing not OPEN | `{"detail": "Listing is not open"}` |
| 403 | Not asker company | `{"detail": "You are not the owner of this ask"}` |
| 404 | Ask not found | `{"detail": "Ask with ID {id} does not exist"}` |

---

### POST /v1/ask/{ask_id}/transition

**Description:** Transition an ask to a new status.

**When to Use:** Use when withdrawing, suspending, or reactivating an ask.

**Authentication Required:** Yes (Bearer Token)

**Permissions Required:** `UPDATE.INSTRUMENT` + role-based rules

#### Allowed Transitions

| Current Status | New Status | Who Can Do It |
|----------------|------------|---------------|
| ACTIVE | WITHDRAWN | Asker company only |
| ACTIVE | SUSPENDED | Admin only |
| WITHDRAWN | SUSPENDED | Admin only |
| SUSPENDED | ACTIVE | Admin only |

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ask_id` | UUID | The unique identifier of the ask |

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | AskStatus | Yes | Target status |

**Example Request:**
```json
{
  "status": "WITHDRAWN"
}
```

#### Response

**Success (200 OK):** Updated Ask object

#### Error Responses

| Code | Condition | Response |
|------|-----------|----------|
| 403 | Invalid transition | `{"detail": "Cannot transition from {status} to {status}"}` |
| 403 | Listing not OPEN | `{"detail": "Listing is not open"}` |
| 404 | Ask not found | `{"detail": "Ask with ID {id} does not exist"}` |

---

## Appendix: Enum Values Reference

### UserRole
| Value | Description |
|-------|-------------|
| `ADMIN` | Full system access |
| `BUYER` | Can purchase instruments |
| `SELLER` | Can sell instruments |
| `ISSUER` | Can issue instruments |

### ActivationStatus
| Value | Description |
|-------|-------------|
| `ACTIVE` | User is fully active |
| `INACTIVE` | User exists but is not currently active |
| `PENDING` | Waiting for email/phone verification |
| `SUSPENDED` | Temporarily disabled by admins |
| `DISABLED` | Permanently disabled by admins |
| `DELETED` | Soft-deleted (account removed but recoverable) |

### AddressType
| Value | Description |
|-------|-------------|
| `REGISTERED` | Registered business address |
| `BILLING` | Billing/invoicing address |
| `OFFICE` | Office/headquarters address |
| `SHIPPING` | Shipping/delivery address |
| `OTHER` | Other address type |

### InstrumentStatus
| Value | Description |
|-------|-------------|
| `DRAFT` | Initial state, can be edited |
| `PENDING_APPROVAL` | Submitted for review |
| `ACTIVE` | Approved and available |
| `MATURED` | Past maturity date |
| `REJECTED` | Declined by reviewer |

### MaturityStatus
| Value | Description |
|-------|-------------|
| `NOT_DUE` | Not yet due for settlement |
| `DUE` | Due for settlement |
| `SETTLED` | Payment has been made |
| `DEFAULTED` | Payment was not made on time |

### TradingStatus
| Value | Description |
|-------|-------------|
| `DRAFT` | Not available for trading |
| `OPEN` | Open for trading |
| `HALTED` | Trading temporarily suspended |
| `CLOSED` | Trading closed |

### ListingStatus
| Value | Description |
|-------|-------------|
| `OPEN` | Listing is active and available |
| `WITHDRAWN` | Voluntarily withdrawn by seller |
| `SUSPENDED` | Suspended by admin/platform |
| `CLOSED` | Successfully completed |

### BidStatus
| Value | Description |
|-------|-------------|
| `PENDING` | Bid is active and awaiting decision |
| `WITHDRAWN` | Voluntarily withdrawn by bidder |
| `SUSPENDED` | Suspended by admin/platform |
| `SELECTED` | Bid was accepted by seller |
| `NOT_SELECTED` | Bid was not selected |

### AskStatus
| Value | Description |
|-------|-------------|
| `ACTIVE` | Ask is active |
| `WITHDRAWN` | Voluntarily withdrawn by asker |
| `SUSPENDED` | Suspended by admin/platform |

### ExecutionMode
| Value | Description |
|-------|-------------|
| `MANUAL` | Bids require manual review |
| `AUTO` | Matching bids are automatically accepted |
