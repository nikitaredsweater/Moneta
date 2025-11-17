"""
module that checks user's permissions on the platform based on the account
status
"""

import app.schemas as schemas
from app.enums import ActivationStatus


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
    return user.account_status in whitelist
