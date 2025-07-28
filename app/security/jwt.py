"""
JWT module
"""

from datetime import datetime, timedelta
from typing import Optional

from jose import jwt

# Load your keys securely
with open('app/keys/private_key.pem', 'r', encoding='utf-8') as f:
    PRIVATE_KEY = f.read()
with open('app/keys/public_key.pem', 'r', encoding='utf-8') as f:
    PUBLIC_KEY = f.read()

ALGORITHM = 'RS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 15


# TODO: When user roles are immplemented update this role field
def create_access_token(
    user_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Creates a JWT token for a user.

    Args:
        user_id: User's id
        role: role
        expires_delta: delta for which the token is
            valid. Default is 15 minutes

    Returns:
        (str) - The Token
    """
    now = datetime.utcnow()
    expire = now + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode = {
        'sub': user_id,
        'role': 'TEST_ROLE',
        'iat': now.timestamp(),
        'exp': expire.timestamp(),
    }

    encoded_jwt = jwt.encode(to_encode, PRIVATE_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> dict:
    """
    Verifies the token by parsing it.

    Args:
        token: JWT token

    Returns:
        (dict) parsed token
    """
    payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
    return payload
