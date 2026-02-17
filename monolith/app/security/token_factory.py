"""
Token factory for creating JWT tokens from user objects.

This module provides a convenience wrapper around moneta-auth's create_access_token
that accepts a user object and automatically populates the expanded JWT claims.
"""

from datetime import timedelta
from typing import Optional, Union
from uuid import UUID

import logging

logger = logging.getLogger(__name__)

from moneta_auth import (
    create_access_token as _create_access_token,
    get_permissions_for_role,
    DEFAULT_EXPIRATION_TIMEDELTA,
)

from app.schemas import MonetaID


def create_access_token(
    user_id: Union[MonetaID, UUID, str],
    expires_delta: Optional[timedelta] = None,
    *,
    role=None,
    company_id=None,
    account_status=None,
) -> str:
    """
    Create a JWT access token for a user.

    This is a convenience wrapper that accepts either just a user_id (for backward
    compatibility) or the full set of claims needed for the expanded JWT.

    Args:
        user_id: User's unique identifier (UUID or string).
        expires_delta: Token lifetime. Defaults to 15 minutes.
        role: User's role (UserRole enum). Required for expanded tokens.
        company_id: User's company ID (optional).
        account_status: User's account status (ActivationStatus enum).
                       Required for expanded tokens.

    Returns:
        Signed JWT token string with expanded claims.

    Raises:
        ValueError: If role or account_status are not provided.
        RuntimeError: If private key is not loaded.

    Example:
        # From auth endpoint after verifying credentials:
        token = create_access_token(
            user_id=user.id,
            role=user.role,
            company_id=user.company_id,
            account_status=user.account_status,
        )
    """
    if role is None:
        raise ValueError(
            "role is required for token creation. "
            "Pass the user's role (e.g., UserRole.BUYER)."
        )

    if account_status is None:
        raise ValueError(
            "account_status is required for token creation. "
            "Pass the user's account status (e.g., ActivationStatus.ACTIVE)."
        )

    # Convert user_id to string if needed
    user_id_str = str(user_id)

    # Convert company_id to string if provided
    company_id_str = str(company_id) if company_id else None

    # Get permissions for the user's role
    permissions = list(get_permissions_for_role(role))

    logger.debug(
    "[SYSTEM] access token data accumulated: user_id=%s, role=%s, company_id=%s, permissions=%s, account_status=%s, expires_delta=%s",
        user_id_str, 
        role, 
        company_id_str, 
        permissions, 
        account_status, 
        expires_delta or DEFAULT_EXPIRATION_TIMEDELTA
    )

    return _create_access_token(
        user_id=user_id_str,
        role=role,
        company_id=company_id_str,
        permissions=permissions,
        account_status=account_status,
        expires_delta=expires_delta or DEFAULT_EXPIRATION_TIMEDELTA,
    )
