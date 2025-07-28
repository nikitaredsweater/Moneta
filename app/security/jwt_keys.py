""""
module that loads the JWT Keys from .env file
"""

import os
from typing import Optional

PRIVATE_KEY: Optional[str] = None
PUBLIC_KEY: Optional[str] = None


def load_jwt_keys() -> None:
    """
    Loads the RSA private and public keys from environment
    variables and stores them in module-level variables for global access.

    Raises:
        RuntimeError: If either key is missing.
    """
    global PRIVATE_KEY, PUBLIC_KEY

    PRIVATE_KEY = os.getenv('JWT_PRIVATE_KEY')
    PUBLIC_KEY = os.getenv('JWT_PUBLIC_KEY')

    if not PRIVATE_KEY or not PUBLIC_KEY:
        raise RuntimeError(
            'Missing JWT_PRIVATE_KEY or JWT_PUBLIC_KEY in environment'
        )

    # Optional: basic validation
    if 'PRIVATE KEY' not in PRIVATE_KEY or 'PUBLIC KEY' not in PUBLIC_KEY:
        raise RuntimeError('Invalid key format detected in environment')
