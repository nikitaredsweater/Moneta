"""
module that checks user's permissions on the platform based on the account
status
"""

import logging

import app.schemas as schemas
from app.enums import ActivationStatus

logger = logging.getLogger(__name__)


def can_get_jwt_token(user: schemas.UserInternal) -> bool:
    """
    Checks if the user's account allows them to get JWT token.
    User's set account_state is compared to a whitelist of allowed statuses for
    this transaction.

    Args:
        user (app.schemas.UserInternal): internal user object

    Returns:
        (bool) True if the user.account_state is in the whitelist
    """
    whitelist = [ActivationStatus.ACTIVE]
    can_get_token = user.account_status in whitelist

    if not can_get_token:
        logger.debug(
            '[AUTH] JWT token denied due to account status | user_id=%s | '
            'account_status=%s',
            user.id,
            user.account_status,
        )
    else:
        logger.debug(
            '[AUTH] JWT token allowed | user_id=%s | account_status=%s',
            user.id,
            user.account_status,
        )

    return can_get_token
