"""
JWT module
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt

from app.schemas.base import MonetaID
from app.security.jwt_keys import jwt_keys

# Don't store keys as module-level variables - access them when needed
ALGORITHM = 'RS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 15


def create_access_token(
    user_id: MonetaID,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Creates a JWT token for a user.

    Args:
        user_id: User's id MonetaID format
        expires_delta: delta for which the token is
            valid. Default is 15 minutes

    Returns:
        str: The JWT token

    Raises:
        RuntimeError: If private key is not available
        Exception: If token encoding fails
    """
    # Use timezone-aware datetime
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # Use integer timestamps for JWT standard compliance
    to_encode = {
        'sub': str(user_id),
        'iat': int(now.timestamp()),
        'exp': int(expire.timestamp()),
    }

    try:
        # Get the private key when needed (not at module load time)
        private_key = jwt_keys.private_key
        encoded_jwt = jwt.encode(to_encode, private_key, algorithm=ALGORITHM)
        return encoded_jwt
    except RuntimeError as e:
        raise RuntimeError(f'Failed to create access token: {e}')
    except Exception as e:
        raise Exception(f'Token encoding failed: {e}')


def verify_access_token(token: str) -> dict:
    """
    Verifies the token by parsing it.

    Args:
        token: JWT token

    Returns:
        dict: Parsed token payload

    Raises:
        RuntimeError: If public key is not available
        Exception: If token verification fails
    """
    try:
        # Get the public key when needed (not at module load time)
        public_key = jwt_keys.public_key
        payload = jwt.decode(token, public_key, algorithms=[ALGORITHM])
        return payload
    except RuntimeError as e:
        raise RuntimeError(f'Failed to verify access token: {e}')
    except Exception as e:
        raise Exception(f'Token verification failed: {e}')


def get_token_payload(token: str) -> Optional[dict]:
    """
    Safely extracts payload from token without verification.
    Useful for debugging or extracting expired token data.

    Args:
        token: JWT token

    Returns:
        dict: Token payload or None if extraction fails
    """
    try:
        # Decode without verification for debugging
        return jwt.get_unverified_claims(token)
    except Exception:
        return None
