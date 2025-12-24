# Authentication Architecture

This document describes the authentication and authorization pattern used across the Moneta backend services.

## Overview

Moneta uses a **distributed JWT authentication** model where:

- **Monolith** is the sole **JWT token factory** (creates and signs tokens)
- **All other services** are **token verifiers** (validate tokens using the public key)

This pattern enables stateless authentication across microservices without requiring database access or inter-service calls for authorization decisions.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Authentication Flow                          │
└─────────────────────────────────────────────────────────────────────┘

  User                    Monolith                    Other Services
   │                         │                              │
   │  1. POST /v1/auth/login │                              │
   │  (email + password)     │                              │
   │────────────────────────>│                              │
   │                         │                              │
   │  2. JWT Token           │                              │
   │  (signed with           │                              │
   │   PRIVATE key)          │                              │
   │<────────────────────────│                              │
   │                         │                              │
   │  3. Request + JWT       │                              │
   │─────────────────────────┼─────────────────────────────>│
   │                         │                              │
   │                         │     4. Verify signature      │
   │                         │        (using PUBLIC key)    │
   │                         │        Extract claims        │
   │                         │        Check permissions     │
   │                         │                              │
   │  5. Response            │                              │
   │<────────────────────────┼──────────────────────────────│
```

## Key Distribution

### RSA Key Pair

The system uses **RS256** (RSA with SHA-256) for JWT signing:

| Key | Location | Used By | Purpose |
|-----|----------|---------|---------|
| Private Key | Monolith only | Token creation | Sign new JWT tokens |
| Public Key | All services | Token verification | Verify JWT signatures |

### Docker Configuration

Keys are distributed via Docker volume mounts:

```yaml
# Monolith - needs BOTH keys (creates and verifies tokens)
services:
  app:
    volumes:
      - ./monolith/app/keys/jwt_private.pem:/app/keys/jwt_private.pem:ro
      - ./monolith/app/keys/jwt_public.pem:/app/keys/jwt_public.pem:ro
    environment:
      - JWT_PRIVATE_KEY_PATH=/app/keys/jwt_private.pem
      - JWT_PUBLIC_KEY_PATH=/app/keys/jwt_public.pem

# Other services - need only PUBLIC key
  other-service:
    volumes:
      - ./monolith/app/keys/jwt_public.pem:/app/keys/jwt_public.pem:ro
    environment:
      - JWT_PUBLIC_KEY_PATH=/app/keys/jwt_public.pem
```

### Generating New Keys

If you need to generate a new RSA key pair:

```bash
# Generate private key (2048-bit RSA)
openssl genrsa -out jwt_private.pem 2048

# Extract public key from private key
openssl rsa -in jwt_private.pem -pubout -out jwt_public.pem
```

## JWT Token Structure

Tokens follow the standard JWT format with three parts: `header.payload.signature`

### Header

```json
{
  "alg": "RS256",
  "typ": "JWT"
}
```

### Payload (Claims)

| Claim | Type | Description |
|-------|------|-------------|
| `sub` | string | User ID (UUID) |
| `role` | string | User role: `ADMIN`, `BUYER`, `SELLER`, `ISSUER` |
| `company_id` | string \| null | Company ID (UUID) or null if unassigned |
| `permissions` | string[] | List of permission strings (e.g., `["VIEW.COMPANY", "UPDATE.INSTRUMENT"]`) |
| `account_status` | string | Account status: `ACTIVE`, `SUSPENDED`, `BANNED`, etc. |
| `iat` | number | Issued at (Unix timestamp) |
| `exp` | number | Expiration (Unix timestamp) |
| `jti` | string | JWT ID (UUID) for potential token revocation |

### Example Decoded Token

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "role": "ISSUER",
  "company_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "permissions": [
    "VIEW.COMPANY",
    "UPDATE.COMPANY",
    "VIEW.COMPANY_ADDRESS",
    "CREATE.COMPANY_ADDRESS",
    "UPDATE.COMPANY_ADDRESS",
    "DELETE.COMPANY_ADDRESS",
    "VIEW.INSTRUMENT",
    "UPDATE.INSTRUMENT"
  ],
  "account_status": "ACTIVE",
  "iat": 1703424000,
  "exp": 1703424900,
  "jti": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

## Service Integration

### Using moneta-auth Package

All services use the `moneta-auth` package for authentication:

```python
# Verification-only service (most microservices)
from moneta_auth import jwt_keys, verify_access_token

jwt_keys.load_public_key()  # Only public key needed

# In request handler or middleware
claims = verify_access_token(token)
user_id = claims.user_id
role = claims.role
permissions = claims.permissions
```

```python
# Token-issuing service (monolith only)
from moneta_auth import jwt_keys, create_access_token, get_permissions_for_role

jwt_keys.load_keys()  # Both keys needed

permissions = get_permissions_for_role(user.role)
token = create_access_token(
    user_id=str(user.id),
    role=user.role,
    company_id=str(user.company_id),
    permissions=list(permissions),
    account_status=user.account_status,
)
```

### FastAPI Middleware

The package provides ready-to-use middleware:

```python
from moneta_auth import JWTAuthMiddleware, jwt_keys

jwt_keys.load_public_key()
app.add_middleware(JWTAuthMiddleware)
```

After middleware processing, request state contains:
- `request.state.token_claims` - Full TokenClaims object
- `request.state.user_id` - User ID string
- `request.state.role` - UserRole enum
- `request.state.company_id` - Company ID string or None

### Permission Checking

```python
from moneta_auth import has_permission, Permission, PermissionVerb, PermissionEntity

@router.get("/users")
async def get_users(
    _=Depends(has_permission([
        Permission(PermissionVerb.VIEW, PermissionEntity.ALL_USERS)
    ]))
):
    # Only users with VIEW.ALL_USERS permission can access
    ...
```

## Role-Based Permissions

Default permission mappings:

| Role | Permissions |
|------|-------------|
| ADMIN | Full access to all entities |
| ISSUER | VIEW/UPDATE company, full COMPANY_ADDRESS access, VIEW/UPDATE instruments |
| BUYER | VIEW company, company addresses, instruments |
| SELLER | VIEW company, company addresses, instruments |

## Token Lifecycle

1. **Creation**: User authenticates via `POST /v1/auth/login`
2. **Expiration**: Tokens expire after 15 minutes (configurable)
3. **Verification**: Each request verifies token signature and expiration
4. **Rejection**: Expired or invalid tokens return 401 Unauthorized

## Security Considerations

- Private key must **never** leave the monolith service
- Public key can be freely distributed to all services
- Tokens are stateless - no revocation mechanism by default
- The `jti` claim enables future token revocation if needed
- Account status is checked on every request (inactive accounts are rejected with 403)

## Further Documentation

For complete API reference and implementation details, see the moneta-auth package repository:

**https://github.com/adtimokhin/moneta-auth**
