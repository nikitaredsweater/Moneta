# Monolith Service

The Monolith Service is the core backend service for the Moneta financial platform, handling user management, company data, financial instruments, and document metadata management.

## Table of Contents

- [Setup Instructions](#setup-instructions)
  - [Protocol Buffer Generation](#protocol-buffer-generation)
  - [Database Migrations](#database-migrations)
  - [Virtual Environment Setup](#virtual-environment-setup)
  - [JWT Key Generation](#jwt-key-generation)
- [API Documentation](#api-documentation)
  - [Authentication](#authentication)
  - [User Management](#user-management)
  - [Company Management](#company-management)
  - [Company Address Management](#company-address-management)
  - [Instrument Management](#instrument-management)
  - [Document Management](#document-management)

## Setup Instructions

### Protocol Buffer Generation (gRPC communication)

1. Navigate to the monolith root directory:

   ```bash
   cd [project_location]/monolith
   ```

2. Activate the virtual environment:

   ```bash
   source venv/bin/activate
   ```

3. Run the proto generation script:

   ```bash
   ./scripts/generate_protos.sh
   ```

4. Fix the import in the generated gRPC file:
   - Open `app/gen/document_ingest_pb2_grpc.py`
   - Find the line:
     ```python
     import gen.document_ingest_pb2 as document__ingest__pb2
     ```
   - Change it to:
     ```python
     import app.gen.document_ingest_pb2 as document__ingest__pb2
     ```

### Database Migrations

To upgrade the SQL database using Alembic:

1. Navigate to the monolith root directory
2. Run:
   ```bash
   alembic upgrade head
   ```

For detailed migration instructions, see [alembic/README.md](alembic/README.md).

### Virtual Environment Setup

When not using Docker:

1. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

2. Activate the environment:

   ```bash
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### JWT Key Generation

1. Generate RSA keys:

   ```bash
   openssl genrsa -out app/keys/jwt_private.pem 2048
   openssl rsa -in app/keys/jwt_private.pem -pubout -out app/keys/jwt_public.pem
   ```

2. Set environment variables in your `.env` file:
   ```bash
   JWT_PRIVATE_KEY_PATH=app/keys/jwt_private.pem
   JWT_PUBLIC_KEY_PATH=app/keys/jwt_public.pem
   ```

## Enumerations

This section lists all enumeration types used in the API requests and responses.

### Address Types

Used in company address management to specify the type of address.

- `REGISTERED` - Official registered address
- `BILLING` - Address for billing purposes
- `OFFICE` - Office location address
- `SHIPPING` - Shipping address
- `OTHER` - Other types of addresses

### Instrument Status

Used in financial instrument management to indicate the current trading status.

- `DRAFT` - Instrument is in draft state, not yet active
- `PENDING_APPROVAL` - Instrument is pending approval for trading
- `ACTIVE` - Instrument is actively trading
- `MATURED` - Instrument has reached maturity

### Maturity Status

Used to indicate the settlement status of financial instruments.

- `NOT_TRADING` - Instrument is not yet publicly tradable
- `PENDING` - Instrument is before maturity date
- `SETTLED` - Instrument has been paid in full
- `DEFAULTED` - Instrument failed to settle

### Order Types

Used for trading order classifications.

- `SELL` - Sell order
- `BUY` - Buy order
- `CANCEL` - Cancel order
- `MODIFY` - Modify existing order

### User Roles

Defines the role and permissions level of users in the system.

- `ADMIN` - Full system administrator access
- `BUYER` - Can buy financial instruments
- `SELLER` - Can sell financial instruments
- `ISSUER` - Can issue new financial instruments

### Permissions

#### Permission Verbs

Actions that can be performed on entities:

- `VIEW` - Read/view permissions
- `CREATE` - Create new entities
- `UPDATE` - Modify existing entities
- `DELETE` - Remove entities
- `ASSIGN` - Assign entities to users/roles

#### Permission Entities

Entities that can have permissions applied:

- `USER` - User management permissions
- `COMPANY` - Company management permissions
- `COMPANY_ADDRESS` - Company address management permissions
- `ROLE` - Role management permissions
- `ALL_DATA` - Permissions to view all data in the system
- `ALL_USERS` - Permissions to manage all users
- `ALL_ROLES` - Permissions to manage all roles

## API Documentation

Monolith Service exposes a bunch of API endpoints for operations with data.

### Authentication

#### `POST /v1/auth/login`

Authenticates a user and returns a JWT token.

**Request:**

```json
{
  "username": "user@example.com",
  "password": "securepassword"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### User Management

#### `GET /v1/user`

Retrieves a list of all users.

**Response:**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "company_id": "550e8400-e29b-41d4-a716-446655440000",
    "role": "BUYER"
  }
]
```

**Required Permissions:** `VIEW_ALL_USERS`

**Enum Fields (in Response):**

- `role` - User role (see [User Roles](#user-roles) section for possible values)
  - `ADMIN` - Full system administrator access
  - `BUYER` - Can buy financial instruments
  - `SELLER` - Can sell financial instruments
  - `ISSUER` - Can issue new financial instruments

#### `POST /v1/user`

Creates a new user.

**Request:**

```json
{
  "email": "newuser@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "securepassword",
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "BUYER"
}
```

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "newuser@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "BUYER"
}
```

**Required Permissions:** `CREATE_USER` or `CREATE_ALL_USERS`

**Enum Fields:**

- `role` - User role (see [User Roles](#user-roles) section for possible values)
  - `ADMIN` - Full system administrator access
  - `BUYER` - Can buy financial instruments
  - `SELLER` - Can sell financial instruments
  - `ISSUER` - Can issue new financial instruments

### Company Management

#### `GET /v1/company`

Retrieves a list of all companies.

**Response:**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Example Corp",
    "tax_id": "123456789"
  }
]
```

**Required Permissions:** `VIEW_COMPANY`

#### `POST /v1/company`

Creates a new company.

**Request:**

```json
{
  "name": "New Company",
  "tax_id": "987654321"
}
```

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "New Company",
  "tax_id": "987654321"
}
```

**Required Permissions:** `CREATE_COMPANY`

### Company Address Management

#### `GET /v1/company-address`

Retrieves addresses for a company.

**Response:**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "company_id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "REGISTERED",
    "street": "123 Main Street",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "US"
  }
]
```

**Required Permissions:** `VIEW_COMPANY_ADDRESS`

**Enum Fields (in Response):**

- `type` - Address type (see [Address Types](#address-types) section for possible values)
  - `REGISTERED` - Official registered address
  - `BILLING` - Address for billing purposes
  - `OFFICE` - Office location address
  - `SHIPPING` - Shipping address
  - `OTHER` - Other types of addresses

#### `POST /v1/company-address`

Creates a new company address.

**Request:**

```json
{
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "REGISTERED",
  "street": "123 Main Street",
  "city": "New York",
  "state": "NY",
  "postal_code": "10001",
  "country": "US"
}
```

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "REGISTERED",
  "street": "123 Main Street",
  "city": "New York",
  "state": "NY",
  "postal_code": "10001",
  "country": "US"
}
```

**Required Permissions:** `CREATE_COMPANY_ADDRESS`

**Enum Fields:**

- `type` - Address type (see [Address Types](#address-types) section for possible values)
  - `REGISTERED` - Official registered address
  - `BILLING` - Address for billing purposes
  - `OFFICE` - Office location address
  - `SHIPPING` - Shipping address
  - `OTHER` - Other types of addresses

### Instrument Management

#### `GET /v1/instrument`

Retrieves a list of financial instruments.

**Response:**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Bond 2025",
    "face_value": 1000.0,
    "currency": "USD",
    "maturity_date": "2025-12-31",
    "maturity_payment": 1100.0,
    "instrument_status": "ACTIVE",
    "maturity_status": "PENDING",
    "issuer_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_by": "550e8400-e29b-41d4-a716-446655440000"
  }
]
```

**Enum Fields (in Response):**

- `instrument_status` - Current trading status (see [Instrument Status](#instrument-status) section for possible values)
  - `DRAFT` - Instrument is in draft state, not yet active
  - `PENDING_APPROVAL` - Instrument is pending approval for trading
  - `ACTIVE` - Instrument is actively trading
  - `MATURED` - Instrument has reached maturity
- `maturity_status` - Settlement status (see [Maturity Status](#maturity-status) section for possible values)
  - `NOT_TRADING` - Instrument is not yet publicly tradable
  - `PENDING` - Instrument is before maturity date
  - `SETTLED` - Instrument has been paid in full
  - `DEFAULTED` - Instrument failed to settle

#### `POST /v1/instrument`

Creates a new financial instrument.

**Request:**

```json
{
  "name": "Corporate Bond 2025",
  "face_value": 1000.0,
  "currency": "USD",
  "maturity_date": "2025-12-31",
  "maturity_payment": 1100.0
}
```

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Corporate Bond 2025",
  "face_value": 1000.0,
  "currency": "USD",
  "maturity_date": "2025-12-31",
  "maturity_payment": 1100.0,
  "instrument_status": "DRAFT",
  "maturity_status": "NOT_TRADING",
  "issuer_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_by": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Notes:**

- `issuer_id` and `created_by` are automatically set based on the authenticated user
- `instrument_status` defaults to "DRAFT"
- `maturity_status` defaults to "NOT_TRADING"

**Enum Fields (in Response):**

- `instrument_status` - Current trading status (see [Instrument Status](#instrument-status) section for possible values)
  - `DRAFT` - Instrument is in draft state, not yet active
  - `PENDING_APPROVAL` - Instrument is pending approval for trading
  - `ACTIVE` - Instrument is actively trading
  - `MATURED` - Instrument has reached maturity
- `maturity_status` - Settlement status (see [Maturity Status](#maturity-status) section for possible values)
  - `NOT_TRADING` - Instrument is not yet publicly tradable
  - `PENDING` - Instrument is before maturity date
  - `SETTLED` - Instrument has been paid in full
  - `DEFAULTED` - Instrument failed to settle

### Document Management

#### `GET /v1/document`

Retrieves a list of documents.

**Response:**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "contract.pdf",
    "type": "LEGAL"
  }
]
```

## Error Codes and Messages

All API endpoints can return the following HTTP error codes with corresponding messages:

### Common Error Codes

#### `400 Bad Request`

- **Message:** "Invalid request data"
- **Cause:** Request body contains invalid data or missing required fields
- **Example:** Missing required field in POST request

#### `401 Unauthorized`

- **Message:** "Invalid credentials"
- **Cause:** Incorrect email/password combination during login
- **Endpoint:** `POST /v1/auth/login`

#### `403 Forbidden`

- **Message:** "Insufficient permissions"
- **Cause:** User lacks required permissions to access the endpoint
- **Example:** User without `VIEW_USER` permission trying to access `GET /v1/user`

#### `404 Not Found`

- **Message:** "Entity was not found"
- **Cause:** Requested entity (user, company, etc.) does not exist
- **Example:** Requesting a company with non-existent ID

#### `409 Conflict`

- **Message:** "Entity with such unique fields already exists"
- **Cause:** Attempting to create an entity that violates unique constraints
- **Example:** Creating a user with an email that already exists

#### `500 Internal Server Error`

- **Message:** "Failed to save the entity"
- **Cause:** Database operation failed during entity creation/update
- **Example:** Database connection issues or constraint violations

### Endpoint-Specific Errors

#### `POST /v1/user`

- **404 Not Found:** `"Company with ID {company_id} does not exist"`
  - When the specified `company_id` does not exist in the database
- **409 Conflict:** `"Entity with such unique fields already exists"`
  - When attempting to create a user with an email that already exists

#### `POST /v1/company-address`

- **404 Not Found:** `"Company with ID {company_id} does not exist"`
  - When the specified `company_id` does not exist in the database

### Error Response Format

All errors follow this JSON format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Permission-Related Errors

Endpoints that require specific permissions will return `403 Forbidden` with the message "Insufficient permissions" when:

- User is not authenticated (missing/invalid JWT token)
- User lacks the required permission for the operation
- User's role does not have the necessary access level

**Permission Mapping:**

- `VIEW_ALL_USERS` - Required for `GET /v1/user`
- `CREATE_USER` - Required for `POST /v1/user` (or `CREATE_ALL_USERS` for admin access)
- `VIEW_COMPANY` - Required for `GET /v1/company`
- `CREATE_COMPANY` - Required for `POST /v1/company`
- `VIEW_COMPANY_ADDRESS` - Required for `GET /v1/company-address`
- `CREATE_COMPANY_ADDRESS` - Required for `POST /v1/company-address`

## Authentication Requirements

All endpoints except `/v1/auth/login` require authentication via JWT token. Include the token in the Authorization header:

```bash
Authorization: Bearer <your_token>
```
