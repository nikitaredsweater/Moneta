# Insomnia Collections

This folder contains Insomnia API collections for testing the Moneta API.

## Files

### Environments
- **environments/global_environment.yaml** - Global environment with shared variables (import FIRST)

### Collections
- **collections/auth_collection.yaml** - Authentication endpoints (`/v1/auth/*`)
- **collections/user_collection.yaml** - User management endpoints (`/v1/user/*`)
- **collections/company_collection.yaml** - Company management endpoints (`/v1/company/*`)
- **collections/company_address_collection.yaml** - Company address endpoints (`/v1/company-address/*`)
- **collections/instrument_collection.yaml** - Instrument management endpoints (`/v1/instrument/*`)
- **collections/listing_collection.yaml** - Listing management endpoints (`/v1/listing/*`)
- **collections/bid_collection.yaml** - Bid management endpoints (`/v1/bid/*`)
- **collections/ask_collection.yaml** - Ask management endpoints (`/v1/ask/*`)

## How to Import

### Step 1: Import the Global Environment (do this first!)

1. Open Insomnia
2. Click on the **Import** button (or `Ctrl+I` / `Cmd+I`)
3. Select **From File**
4. Import `global_environment.yaml`
5. This creates the **Moneta Global** environment with all shared variables

### Step 2: Import Collections

1. Import all collection files from `collections/` folder
2. For each collection, go to **Manage Environments**
3. Set the base environment to inherit from **Moneta Global**

### Step 3: Activate the Global Environment

1. Click the environment dropdown (top-left of any collection)
2. Select **Moneta Global** as your active environment
3. All collections will now share the same variables

## Global Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `base_url` | API base URL | `http://localhost:8080` |
| `api_version` | API version | `v1` |
| `admin_email` | Admin login email | `admin@example.com` |
| `admin_password` | Admin login password | `password123` |
| `admin_token` | JWT token (set after login) | `` |
| `test_email` | Test user email | `test@example.com` |
| `test_password` | Test user password | `TestPassword123!` |
| `test_user_id` | UUID for testing user endpoints | `` |
| `test_company_id` | UUID for testing company endpoints | `` |
| `test_instrument_id` | UUID for testing instrument endpoints | `` |
| `test_document_id` | UUID for testing document association | `` |
| `test_listing_id` | UUID for testing listing endpoints | `` |
| `test_bid_id` | UUID for testing bid endpoints | `` |
| `test_ask_id` | UUID for testing ask endpoints | `` |

## Auth Collection Endpoints

| Request | Method | Path | Description |
|---------|--------|------|-------------|
| Login | POST | `/v1/auth/login` | Authenticate and get JWT token |
| Login - Invalid Email | POST | `/v1/auth/login` | Test with non-existent email (expects 401) |
| Login - Invalid Password | POST | `/v1/auth/login` | Test with wrong password (expects 401) |
| Login - Missing Fields | POST | `/v1/auth/login` | Test with missing fields (expects 422) |

## Using the Token

After a successful admin login, copy the `access_token` from the response and set it in the `admin_token` environment variable:

1. Run the **Login - Admin** request
2. Copy the `access_token` from the response
3. Go to **Manage Environments** (click environment dropdown, top-left)
4. Paste the token into the `admin_token` field
5. All authenticated requests will now use this token automatically

The `admin_token` variable is in the global environment, so it's shared across all collections.

## User Collection Endpoints

**Note:** All user endpoints require Bearer token authentication. Run the Admin Login from auth_collection first and set the `admin_token` environment variable.

| Request | Method | Path | Description | Permission |
|---------|--------|------|-------------|------------|
| Get All Users | GET | `/v1/user/` | Get all users | VIEW.ALL_USERS |
| Search Users | POST | `/v1/user/search` | Search with filters | VIEW.ALL_USERS |
| Get User by ID | GET | `/v1/user/{id}` | Get specific user | VIEW.USER |
| Create User | POST | `/v1/user/` | Create new user | CREATE.USER |
| Patch User | PATCH | `/v1/user/{id}` | Update user fields | UPDATE.USER |
| Delete User | DELETE | `/v1/user/{id}` | Delete a user | DELETE.USER |

### User Collection Environment Variables

- `admin_token`: JWT token from admin login (required for all authenticated requests)
- `test_user_id`: UUID of a user to test GET/PATCH/DELETE operations
- `test_company_id`: UUID of a company for creating users

### Available Roles

- `ADMIN` - Full system access
- `BUYER` - Can purchase instruments
- `SELLER` - Can sell instruments
- `ISSUER` - Can issue instruments

### Available Account Statuses

- `ACTIVE` - Account is active
- `INACTIVE` - Account is inactive
- `PENDING` - Account is pending activation
- `SUSPENDED` - Account is suspended

## Company Collection Endpoints

**Note:** All company endpoints require Bearer token authentication.

| Request | Method | Path | Description | Permission |
|---------|--------|------|-------------|------------|
| Get All Companies | GET | `/v1/company/` | Get all companies | VIEW.COMPANY |
| Search Companies | POST | `/v1/company/search` | Search with filters | VIEW.COMPANY |
| Get Company by ID | GET | `/v1/company/{id}` | Get specific company | VIEW.COMPANY |
| Create Company | POST | `/v1/company/` | Create new company | CREATE.COMPANY |

### Company Include Options

When fetching a company by ID, you can include related entities using the `?include=` query parameter:

| Include | Description |
|---------|-------------|
| `addresses` | Company addresses |
| `users` | Users belonging to the company |
| `instruments` | Instruments issued by the company |

**Examples:**
- `?include=addresses` - Include addresses only
- `?include=users` - Include users only
- `?include=instruments` - Include instruments only
- `?include=addresses,users` - Include addresses and users
- `?include=addresses,instruments` - Include addresses and instruments
- `?include=users,instruments` - Include users and instruments
- `?include=addresses,users,instruments` - Include all

### Company Search Filters

| Filter | Type | Description |
|--------|------|-------------|
| `legalName` | string | Partial match on legal name |
| `tradeName` | string | Partial match on trade name |
| `registrationNumber` | string | Partial match on registration number |
| `incorporationDateAfter` | date | Companies incorporated after this date |
| `incorporationDateBefore` | date | Companies incorporated before this date |
| `createdAtAfter` | date | Companies created after this date |
| `createdAtBefore` | date | Companies created before this date |
| `sort` | string | Sort order (e.g., `-createdAt,legalName`) |
| `limit` | int | Results per page (default: 50, max: 200) |
| `offset` | int | Pagination offset (default: 0) |

## Company Address Collection Endpoints

**Note:** All company address endpoints require Bearer token authentication.

| Request | Method | Path | Description | Permission |
|---------|--------|------|-------------|------------|
| Get All Company Addresses | GET | `/v1/company-address/` | Get all addresses | VIEW.COMPANY_ADDRESS |
| Create Company Address - Registered | POST | `/v1/company-address/` | Create registered address | CREATE.COMPANY_ADDRESS |
| Create Company Address - Billing | POST | `/v1/company-address/` | Create billing address | CREATE.COMPANY_ADDRESS |
| Create Company Address - Office | POST | `/v1/company-address/` | Create office address | CREATE.COMPANY_ADDRESS |
| Create Company Address - Shipping | POST | `/v1/company-address/` | Create shipping address | CREATE.COMPANY_ADDRESS |
| Create Company Address - Other | POST | `/v1/company-address/` | Create other address type | CREATE.COMPANY_ADDRESS |
| Create Company Address - International (UK) | POST | `/v1/company-address/` | Create international address | CREATE.COMPANY_ADDRESS |

### Address Types

- `REGISTERED` - Registered business address
- `BILLING` - Billing/invoicing address
- `OFFICE` - Office/headquarters address
- `SHIPPING` - Shipping/delivery address
- `OTHER` - Other address type

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `type` | AddressType | One of: REGISTERED, BILLING, OFFICE, SHIPPING, OTHER |
| `street` | string | Street address |
| `city` | string | City name |
| `postalCode` | string | Postal/ZIP code |
| `country` | string | ISO 3166-1 alpha-2 country code (e.g., "US", "GB") |
| `companyId` | UUID | Company this address belongs to |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `state` | string | State/province (optional for some countries) |

## Instrument Collection Endpoints

**Note:** All instrument endpoints require Bearer token authentication.

| Request | Method | Path | Description | Permission |
|---------|--------|------|-------------|------------|
| Search Instruments | POST | `/v1/instrument/search` | Search with filters | VIEW.INSTRUMENT |
| Get Instrument by ID | GET | `/v1/instrument/{id}` | Get specific instrument | VIEW.INSTRUMENT |
| Get Instrument with Documents | GET | `/v1/instrument/{id}?include=documents` | Get instrument with documents | VIEW.INSTRUMENT |
| Create Instrument | POST | `/v1/instrument/` | Create new instrument | CREATE.INSTRUMENT |
| Update Draft Instrument | PATCH | `/v1/instrument/{id}` | Update instrument in DRAFT status | UPDATE.INSTRUMENT |
| Transition: Submit for Approval | POST | `/v1/instrument/{id}/transition` | DRAFT → PENDING_APPROVAL | UPDATE.INSTRUMENT |
| Transition: Approve | POST | `/v1/instrument/{id}/transition` | PENDING_APPROVAL → ACTIVE | APPROVE.INSTRUMENT |
| Transition: Reject | POST | `/v1/instrument/{id}/transition` | PENDING_APPROVAL → REJECTED | APPROVE.INSTRUMENT |
| Associate Document | POST | `/v1/instrument/{id}/documents/{document_id}` | Link document to instrument | UPDATE.INSTRUMENT |

### Instrument Status Values

| Status | Description |
|--------|-------------|
| `DRAFT` | Initial state, can be edited |
| `PENDING_APPROVAL` | Submitted for review |
| `ACTIVE` | Approved and available |
| `REJECTED` | Declined by reviewer |

### Instrument Status Transitions

| From | To | Required Permission |
|------|-----|---------------------|
| DRAFT | PENDING_APPROVAL | UPDATE.INSTRUMENT |
| PENDING_APPROVAL | ACTIVE | APPROVE.INSTRUMENT |
| PENDING_APPROVAL | REJECTED | APPROVE.INSTRUMENT |

### Maturity Status Values

- `NOT_MATURED` - Not yet matured
- `MATURED` - Has reached maturity
- `EXTENDED` - Maturity extended

### Trading Status Values

- `OPEN` - Open for trading
- `HALTED` - Trading temporarily suspended
- `CLOSED` - Trading closed

### Instrument Search Filters

| Filter | Type | Description |
|--------|------|-------------|
| `name` | string | Partial match on instrument name |
| `isin` | string | Partial match on ISIN code |
| `status` | InstrumentStatus | Filter by status |
| `maturityStatus` | MaturityStatus | Filter by maturity status |
| `tradingStatus` | TradingStatus | Filter by trading status |
| `issueDateAfter` | date | Instruments issued after this date |
| `issueDateBefore` | date | Instruments issued before this date |
| `maturityDateAfter` | date | Instruments maturing after this date |
| `maturityDateBefore` | date | Instruments maturing before this date |
| `faceValueMin` | decimal | Minimum face value |
| `faceValueMax` | decimal | Maximum face value |
| `interestRateMin` | decimal | Minimum interest rate |
| `interestRateMax` | decimal | Maximum interest rate |
| `companyId` | UUID | Filter by issuing company |
| `sort` | string | Sort order (e.g., `-createdAt,name`) |
| `limit` | int | Results per page (default: 50) |
| `offset` | int | Pagination offset (default: 0) |

## Listing Collection Endpoints

**Note:** All listing endpoints require Bearer token authentication.

| Request | Method | Path | Description | Permission |
|---------|--------|------|-------------|------------|
| Search Listings | POST | `/v1/listing/search` | Search with filters | VIEW.INSTRUMENT |
| Search Listings with Instrument | POST | `/v1/listing/search?include=instrument` | Search with instrument included | VIEW.INSTRUMENT |
| Get Listing by ID | GET | `/v1/listing/{id}` | Get specific listing | VIEW.INSTRUMENT |
| Get Listing with Instrument | GET | `/v1/listing/{id}?include=instrument` | Get listing with instrument | VIEW.INSTRUMENT |
| Create Listing | POST | `/v1/listing/` | Create new listing | UPDATE.INSTRUMENT |
| Transition: Withdraw | POST | `/v1/listing/{id}/transition` | OPEN → WITHDRAWN | UPDATE.INSTRUMENT |
| Transition: Suspend (Admin) | POST | `/v1/listing/{id}/transition` | OPEN → SUSPENDED | UPDATE.INSTRUMENT + ADMIN |
| Transition: Close (Admin) | POST | `/v1/listing/{id}/transition` | OPEN → CLOSED | UPDATE.INSTRUMENT + ADMIN |

### Listing Status Values

| Status | Description |
|--------|-------------|
| `OPEN` | Listing is active and available for trading |
| `WITHDRAWN` | Listing was voluntarily withdrawn by the seller |
| `SUSPENDED` | Listing was suspended by admin/platform |
| `CLOSED` | Listing has found a bidder and is closed |

### Listing Status Transitions

| From | To | Who Can Do It |
|------|-----|---------------|
| OPEN | WITHDRAWN | Company user (seller) |
| OPEN | SUSPENDED | Admin only |
| OPEN | CLOSED | Admin only |
| SUSPENDED | OPEN | Admin only |
| WITHDRAWN | SUSPENDED | Admin only |

### Listing Search Filters

| Filter | Type | Description |
|--------|------|-------------|
| `instrumentId` | UUID[] | Filter by instrument IDs |
| `sellerCompanyId` | UUID[] | Filter by seller company IDs |
| `listingCreatorUserId` | UUID[] | Filter by creator user IDs |
| `status` | ListingStatus | Filter by status |
| `sort` | string | Sort order (e.g., `-createdAt`) |
| `limit` | int | Results per page (default: 50, max: 200) |
| `offset` | int | Pagination offset (default: 0) |

## Bid Collection Endpoints

**Note:** All bid endpoints require Bearer token authentication.

| Request | Method | Path | Description | Permission |
|---------|--------|------|-------------|------------|
| Search Bids | POST | `/v1/bid/search` | Search with filters | VIEW.INSTRUMENT |
| Search Bids with Listing | POST | `/v1/bid/search?include=listing` | Search with listing included | VIEW.INSTRUMENT |
| Get Bid by ID | GET | `/v1/bid/{id}` | Get specific bid | VIEW.INSTRUMENT |
| Get Bid with Listing | GET | `/v1/bid/{id}?include=listing` | Get bid with listing | VIEW.INSTRUMENT |
| Create Bid | POST | `/v1/bid/` | Create new bid | UPDATE.INSTRUMENT |
| Transition: Withdraw | POST | `/v1/bid/{id}/transition` | PENDING → WITHDRAWN | UPDATE.INSTRUMENT |
| Transition: Suspend (Admin) | POST | `/v1/bid/{id}/transition` | PENDING → SUSPENDED | UPDATE.INSTRUMENT + ADMIN |
| Accept Bid | POST | `/v1/bid/{id}/accept` | Accept bid (seller only) | UPDATE.INSTRUMENT |
| Reject Bid | POST | `/v1/bid/{id}/reject` | Reject bid (seller only) | UPDATE.INSTRUMENT |

### Bid Status Values

| Status | Description |
|--------|-------------|
| `PENDING` | Bid is active and awaiting decision |
| `WITHDRAWN` | Bid was voluntarily withdrawn by the bidder |
| `SUSPENDED` | Bid was suspended by admin/platform |
| `SELECTED` | Bid was selected/accepted by the seller |
| `NOT_SELECTED` | Bid was not selected (rejected or another bid was selected) |

### Bid Status Transitions

| From | To | Who Can Do It |
|------|-----|---------------|
| PENDING | WITHDRAWN | Bidder company |
| PENDING | SUSPENDED | Admin only |
| PENDING | SELECTED | Seller company (via accept) |
| PENDING | NOT_SELECTED | Seller company (via reject) |
| WITHDRAWN | SUSPENDED | Admin only |

### Bid Search Filters

| Filter | Type | Description |
|--------|------|-------------|
| `listingId` | UUID[] | Filter by listing IDs |
| `bidderCompanyId` | UUID[] | Filter by bidder company IDs |
| `bidderUserId` | UUID[] | Filter by bidder user IDs |
| `status` | BidStatus | Filter by status |
| `minAmount` | decimal | Minimum bid amount |
| `maxAmount` | decimal | Maximum bid amount |
| `currency` | string | Filter by currency (ISO 4217) |
| `sort` | string | Sort order (e.g., `-createdAt`) |
| `limit` | int | Results per page (default: 50, max: 200) |
| `offset` | int | Pagination offset (default: 0) |

## Ask Collection Endpoints

**Note:** All ask endpoints require Bearer token authentication.

| Request | Method | Path | Description | Permission |
|---------|--------|------|-------------|------------|
| Search Asks | POST | `/v1/ask/search` | Search with filters | VIEW.INSTRUMENT |
| Search Asks with Listing | POST | `/v1/ask/search?include=listing` | Search with listing included | VIEW.INSTRUMENT |
| Get Ask by ID | GET | `/v1/ask/{id}` | Get specific ask | VIEW.INSTRUMENT |
| Get Ask with Listing | GET | `/v1/ask/{id}?include=listing` | Get ask with listing | VIEW.INSTRUMENT |
| Create Ask (Manual) | POST | `/v1/ask/` | Create ask with manual mode | UPDATE.INSTRUMENT |
| Create Ask (Auto) | POST | `/v1/ask/` | Create ask with auto mode | UPDATE.INSTRUMENT |
| Update Ask | PATCH | `/v1/ask/{id}` | Update ask price/validity | UPDATE.INSTRUMENT |
| Transition: Withdraw | POST | `/v1/ask/{id}/transition` | ACTIVE → WITHDRAWN | UPDATE.INSTRUMENT |
| Transition: Suspend (Admin) | POST | `/v1/ask/{id}/transition` | ACTIVE → SUSPENDED | UPDATE.INSTRUMENT + ADMIN |
| Transition: Reactivate (Admin) | POST | `/v1/ask/{id}/transition` | SUSPENDED → ACTIVE | UPDATE.INSTRUMENT + ADMIN |

### Ask Status Values

| Status | Description |
|--------|-------------|
| `ACTIVE` | Ask is active and accepting bids |
| `WITHDRAWN` | Ask was voluntarily withdrawn by the asker |
| `SUSPENDED` | Ask was suspended by admin/platform |

### Ask Status Transitions

| From | To | Who Can Do It |
|------|-----|---------------|
| ACTIVE | WITHDRAWN | Asker company |
| ACTIVE | SUSPENDED | Admin only |
| WITHDRAWN | SUSPENDED | Admin only |
| SUSPENDED | ACTIVE | Admin only |

### Execution Modes

| Mode | Description |
|------|-------------|
| `MANUAL` | Bids require manual review and acceptance by the seller |
| `AUTO` | Bids matching the ask price are automatically accepted |

### Ask Search Filters

| Filter | Type | Description |
|--------|------|-------------|
| `listingId` | UUID[] | Filter by listing IDs |
| `askerCompanyId` | UUID[] | Filter by asker company IDs |
| `askerUserId` | UUID[] | Filter by asker user IDs |
| `status` | AskStatus | Filter by status |
| `minAmount` | decimal | Minimum ask amount |
| `maxAmount` | decimal | Maximum ask amount |
| `currency` | string | Filter by currency (ISO 4217) |
| `executionMode` | ExecutionMode | Filter by execution mode (AUTO/MANUAL) |
| `binding` | boolean | Filter by binding status |
| `sort` | string | Sort order (e.g., `-createdAt`) |
| `limit` | int | Results per page (default: 50, max: 200) |
| `offset` | int | Pagination offset (default: 0) |
