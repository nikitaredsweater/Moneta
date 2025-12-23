"""
Password encryption security module.

Provides secure password hashing and verification functions using bcrypt.
This module handles password encryption with salt generation and secure
hashing algorithms suitable for user authentication systems.

Note: This module uses one-way hashing (bcrypt) rather than
reversible encryption, which is the security best practice for password storage.
Passwords cannot and should not be decrypted back to plaintext.
"""

import logging

import bcrypt

logger = logging.getLogger(__name__)


def encrypt_password(password: str) -> str:
    """
    Encrypt (hash) a password using bcrypt with salt generation.

    This function takes a plaintext password and generates a secure hash
    using bcrypt with automatic salt generation. The resulting hash includes
    the salt and can be safely stored in a database.

    Args:
        password (str): The plaintext password to encrypt.

    Returns:
        str: The bcrypt hashed password as a string, including salt.

    Example:
        >>> hashed = encrypt_password('my_secure_password')
        >>> print(hashed)
        $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/Lewf.6TaXqQ8H2Jv6

    Raises:
        TypeError: If password is not a string.

    Security Notes:
        - Uses bcrypt with default work factor (12 rounds)
        - Automatically generates a unique salt for each password
        - Resistant to rainbow table and brute force attacks
    """
    logger.debug('[AUTH] Encrypting password')
    if not isinstance(password, str):
        logger.error('[AUTH] Password encryption failed | error=Password must be a string')
        raise TypeError('Password must be a string')

    # Convert string to bytes
    password_bytes = password.encode('utf-8')

    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)

    logger.debug('[AUTH] Password encrypted successfully')
    # Return as string for database storage
    return hashed.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its stored hash.

    This function takes a plaintext password and compares it against
    a previously hashed password to determine if they match. This is
    the 'decryption' equivalent for password verification.

    Args:
        password (str): The plaintext password to verify.
        hashed_password (str): The stored bcrypt hash to verify against.

    Returns:
        bool: True if the password matches the hash, False otherwise.

    Example:
        >>> hashed = encrypt_password('my_secure_password')
        >>> is_valid = verify_password('my_secure_password', hashed)
        >>> print(is_valid)
        True
        >>> is_valid = verify_password('wrong_password', hashed)
        >>> print(is_valid)
        False

    Raises:
        TypeError: If password or hashed_password is not a string.
        ValueError: If hashed_password is not a valid bcrypt hash.

    Security Notes:
        - Uses constant-time comparison to prevent timing attacks
        - Works with any bcrypt hash regardless of work factor
        - Safe against hash format manipulation attacks
    """
    logger.debug('[AUTH] Verifying password')
    if not isinstance(password, str):
        logger.error('[AUTH] Password verification failed | error=Password must be a string')
        raise TypeError('Password must be a string')

    if not isinstance(hashed_password, str):
        logger.error(
            '[AUTH] Password verification failed | error=Hashed password must be a string'
        )
        raise TypeError('Hashed password must be a string')

    try:
        # Convert strings to bytes
        password_bytes = password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')

        # Verify password using bcrypt
        is_valid = bcrypt.checkpw(password_bytes, hashed_bytes)

        if is_valid:
            logger.debug('[AUTH] Password verification successful')
        else:
            logger.debug('[AUTH] Password verification failed | reason=mismatch')

        return is_valid

    except ValueError as e:
        # Re-raise with more specific message
        logger.warning('[AUTH] Invalid bcrypt hash format | error=%s', str(e))
        raise ValueError(f'Invalid bcrypt hash format: {str(e)}')


def is_password_strong(
    password: str, min_length: int = 8
) -> tuple[bool, list[str]]:
    """
    Check if a password meets basic strength requirements.

    Optional utility function to validate password strength before encryption.

    Args:
        password (str): The password to validate.
        min_length (int): Minimum required password length (default: 8).

    Returns:
        tuple[bool, list[str]]: A tuple containing:
            - bool: True if password is strong, False otherwise
            - list[str]: List of requirement violations (empty if strong)

    Example:
        >>> is_strong, issues = is_password_strong('weak')
        >>> print(is_strong, issues)
        False ['Password must be at least 8 characters long',
                'Password must contain uppercase letters', ...]

    Requirements Checked:
        - Minimum length
        - Contains uppercase letters
        - Contains lowercase letters
        - Contains numbers
        - Contains special characters
    """
    if not isinstance(password, str):
        raise TypeError('Password must be a string')

    issues = []

    # Check length
    if len(password) < min_length:
        issues.append(f'Password must be at least {min_length} characters long')

    # Check for uppercase
    if not any(c.isupper() for c in password):
        issues.append('Password must contain uppercase letters')

    # Check for lowercase
    if not any(c.islower() for c in password):
        issues.append('Password must contain lowercase letters')

    # Check for digits
    if not any(c.isdigit() for c in password):
        issues.append('Password must contain numbers')

    # Check for special characters
    special_chars = '!@#$%^&*()_+-=[]{}|;:,.<>?'
    if not any(c in special_chars for c in password):
        issues.append('Password must contain special characters')

    return len(issues) == 0, issues
