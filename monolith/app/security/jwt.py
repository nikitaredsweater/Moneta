"""
JWT module
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.schemas.base import MonetaID
from app.security.jwt_keys import jwt_keys
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

ALGORITHM = 'RS256'
ACCESS_TOKEN_EXPIRE_DEFAULT_MINUTES = 15
ACCESS_TOKEN_EXPIRE_DEFAULT_SECONDS = (
    ACCESS_TOKEN_EXPIRE_DEFAULT_MINUTES * 60_000
)  # Default is 15 minutes
ACCESS_TOKEN_EXPIRE_DEFAULT_TIMEDELTA = timedelta(
    minutes=ACCESS_TOKEN_EXPIRE_DEFAULT_MINUTES
)


def create_access_token(
    user_id: MonetaID,
    expires_delta: timedelta = ACCESS_TOKEN_EXPIRE_DEFAULT_TIMEDELTA,
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
    logger.debug('[AUTH] Creating access token | user_id=%s', user_id)
    # Use timezone-aware datetime
    now = datetime.now(timezone.utc)
    expire = now + expires_delta

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
        logger.info('[AUTH] Access token created | user_id=%s', user_id)
        return encoded_jwt
    except RuntimeError as e:
        logger.error(
            '[AUTH] Failed to create access token | user_id=%s | error=%s',
            user_id,
            str(e),
        )
        raise RuntimeError(f'Failed to create access token: {e}')
    except Exception as e:
        logger.error(
            '[AUTH] Token encoding failed | user_id=%s | error_type=%s | error=%s',
            user_id,
            type(e).__name__,
            str(e),
        )
        raise Exception(f'Token encoding failed: {e}')


def verify_access_token(token: str) -> dict:
    """
    Verifies the token by parsing it.

    Args:
        token: JWT token

    Returns:
        dict: Parsed token payload

    Raises:
        JWTError: If public key is not available or if token verification fails
    """
    logger.debug('[AUTH] Verifying access token')
    try:
        # Get the public key when needed (not at module load time)
        public_key = jwt_keys.public_key
        payload = jwt.decode(token, public_key, algorithms=[ALGORITHM])
        user_id = payload.get('sub', 'unknown')
        logger.debug('[AUTH] Access token verified | user_id=%s', user_id)
        return payload
    except RuntimeError as e:
        logger.warning('[AUTH] Failed to verify access token | error=%s', str(e))
        raise JWTError(f'Failed to verify access token: {e}')
    except Exception as e:
        logger.warning(
            '[AUTH] Token verification failed | error_type=%s | error=%s',
            type(e).__name__,
            str(e),
        )
        raise JWTError(f'Token verification failed: {e}')


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
        payload = jwt.get_unverified_claims(token)
        logger.debug('[AUTH] Token payload extracted (unverified)')
        return payload
    except Exception as e:
        logger.debug(
            '[AUTH] Failed to extract token payload | error_type=%s',
            type(e).__name__,
        )
        return None
