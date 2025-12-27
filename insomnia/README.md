# Insomnia Collections

This folder contains Insomnia API collections for testing the Moneta API.

## Files

- **global_environment.yaml** - Global environment with shared variables (import FIRST)
- **auth_collection.yaml** - Authentication endpoints (`/v1/auth/*`)
- **user_collection.yaml** - User management endpoints (`/v1/user/*`)

## How to Import

### Step 1: Import the Global Environment (do this first!)

1. Open Insomnia
2. Click on the **Import** button (or `Ctrl+I` / `Cmd+I`)
3. Select **From File**
4. Import `global_environment.yaml`
5. This creates the **Moneta Global** environment with all shared variables

### Step 2: Import Collections

1. Import `auth_collection.yaml` and `user_collection.yaml`
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
