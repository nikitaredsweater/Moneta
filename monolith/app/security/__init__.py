"""
Security module

Re-exports authentication and authorization utilities from moneta-auth package.
"""

# Password utilities from moneta-auth
from moneta_auth import encrypt_password, verify_password

# Permission checking from moneta-auth
from moneta_auth import (
    DEFAULT_ROLE_PERMISSIONS as ROLE_PERMISSIONS,
    Permission,
    has_permission,
)

# JWT token management from moneta-auth
from moneta_auth import (
    DEFAULT_EXPIRATION_MINUTES as ACCESS_TOKEN_EXPIRE_DEFAULT_MINUTES,
    DEFAULT_EXPIRATION_SECONDS as ACCESS_TOKEN_EXPIRE_DEFAULT_SECONDS,
    DEFAULT_EXPIRATION_TIMEDELTA as ACCESS_TOKEN_EXPIRE_DEFAULT_TIMEDELTA,
    get_permissions_for_role,
)

# Local wrapper for token creation with user object
from app.security.token_factory import create_access_token

# Local account status check (uses internal UserInternal schema)
from app.security.account_status import can_get_jwt_token

__all__ = [
    'encrypt_password',
    'verify_password',
    'Permission',
    'ROLE_PERMISSIONS',
    'has_permission',
    'create_access_token',
    'get_permissions_for_role',
    'ACCESS_TOKEN_EXPIRE_DEFAULT_MINUTES',
    'ACCESS_TOKEN_EXPIRE_DEFAULT_TIMEDELTA',
    'ACCESS_TOKEN_EXPIRE_DEFAULT_SECONDS',
    'can_get_jwt_token',
]
