"""
Module that loads the JWT Keys from .env file
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class JWTKeyManager:
    """
    Manages RSA private and public keys for JWT operations.
    """

    def __init__(self) -> None:
        self._private_key: Optional[bytes] = None
        self._public_key: Optional[bytes] = None
        self._loaded = False

    def load_keys(self) -> None:
        """
        Loads the RSA private and public keys from environment variables.

        Raises:
            ValueError: If environment variables are not set.
            FileNotFoundError: If key files don't exist.
            RuntimeError: If key files are empty or unreadable.
        """
        private_key_path = os.getenv('JWT_PRIVATE_KEY_PATH')
        public_key_path = os.getenv('JWT_PUBLIC_KEY_PATH')

        if not private_key_path or not public_key_path:
            raise ValueError(
                'JWT_PRIVATE_KEY_PATH or JWT_PUBLIC_KEY_PATH is not set in the .env file'
            )

        private_path = Path(private_key_path)
        public_path = Path(public_key_path)

        # Check if files exist
        if not private_path.exists():
            raise FileNotFoundError(
                f'Private key file not found: {private_key_path}'
            )
        if not public_path.exists():
            raise FileNotFoundError(
                f'Public key file not found: {public_key_path}'
            )

        try:
            # Read the key files as bytes
            with private_path.open('rb') as f:
                self._private_key = f.read()
            with public_path.open('rb') as f:
                self._public_key = f.read()

            # Validate that keys were read and are not empty
            if not self._private_key or not self._public_key:
                raise RuntimeError('One or both key files are empty')

            # Basic validation that the keys contain expected PEM markers
            private_key_str = self._private_key.decode('utf-8', errors='ignore')
            public_key_str = self._public_key.decode('utf-8', errors='ignore')

            if (
                '-----BEGIN' not in private_key_str
                or '-----END' not in private_key_str
            ):
                raise RuntimeError(
                    'Private key file does not appear to be in PEM format'
                )
            if (
                '-----BEGIN' not in public_key_str
                or '-----END' not in public_key_str
            ):
                raise RuntimeError(
                    'Public key file does not appear to be in PEM format'
                )

            self._loaded = True

        except OSError as e:
            raise RuntimeError(f'Error reading key files: {e}')
        except UnicodeDecodeError:
            # Keys should be readable as UTF-8 for PEM format validation
            raise RuntimeError('Key files contain invalid characters')

    @property
    def private_key(self) -> bytes:
        """
        Returns the loaded private key.

        Returns:
            bytes: The private key as bytes.

        Raises:
            RuntimeError: If keys haven't been loaded yet.
        """
        if not self._loaded or self._private_key is None:
            raise RuntimeError('JWT keys not loaded. Call load_keys() first.')
        return self._private_key

    @property
    def public_key(self) -> bytes:
        """
        Returns the loaded public key.

        Returns:
            bytes: The public key as bytes.

        Raises:
            RuntimeError: If keys haven't been loaded yet.
        """
        if not self._loaded or self._public_key is None:
            raise RuntimeError('JWT keys not loaded. Call load_keys() first.')
        return self._public_key

    @property
    def is_loaded(self) -> bool:
        """
        Returns whether the keys have been successfully loaded.

        Returns:
            bool: True if keys are loaded, False otherwise.
        """
        return self._loaded

    def reload_keys(self) -> None:
        """
        Reloads the keys from the file system.
        Useful if the key files have been updated.
        """
        self._private_key = None
        self._public_key = None
        self._loaded = False
        self.load_keys()


# Create a default instance for convenience
jwt_keys = JWTKeyManager()

# Try to load keys on import, but don't fail if it doesn't work
try:
    jwt_keys.load_keys()
except Exception as e:
    print(f'Warning: Failed to load JWT keys on import: {e}')


def load_jwt_keys() -> None:
    """
    Convenience function to load keys using the default instance.
    """
    jwt_keys.load_keys()
