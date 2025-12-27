# Insomnia Collections

This folder contains Insomnia API collections for testing the Moneta API.

## Collections

- **auth_collection.yaml** - Authentication endpoints (`/v1/auth/*`)

## How to Import

1. Open Insomnia
2. Click on the **Import** button (or `Ctrl+I` / `Cmd+I`)
3. Select **From File**
4. Navigate to this folder and select the desired `.yaml` file
5. Click **Import**

## Environments

Each collection includes environments for different setups:

### Base Environment
- `base_url`: `http://localhost:8000`
- `api_version`: `v1`

### Local Development
- Inherits from Base Environment
- `test_email`: `test@example.com`
- `test_password`: `TestPassword123!`

## Customizing Environments

After importing, you can modify environment variables:

1. Click on the environment dropdown (top-left)
2. Select **Manage Environments**
3. Edit the values as needed for your local setup

## Auth Collection Endpoints

| Request | Method | Path | Description |
|---------|--------|------|-------------|
| Login | POST | `/v1/auth/login` | Authenticate and get JWT token |
| Login - Invalid Email | POST | `/v1/auth/login` | Test with non-existent email (expects 401) |
| Login - Invalid Password | POST | `/v1/auth/login` | Test with wrong password (expects 401) |
| Login - Missing Fields | POST | `/v1/auth/login` | Test with missing fields (expects 422) |

## Using the Token

After a successful login, copy the `access_token` from the response and use it in other requests:

1. In any authenticated request, go to the **Auth** tab
2. Select **Bearer Token**
3. Paste the token value

Or add a header manually:
```
Authorization: Bearer <your_token_here>
```
