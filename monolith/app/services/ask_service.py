"""
Ask Service.

This module contains service functions for managing ask operations.
It centralizes all business logic for ask creation, updates, and status changes
to ensure proper validation and consistency.

Key rules:
    - Asks can only be created/updated when the listing is OPEN
    - Asker company must be the same as listing's seller company
    - Asker user must belong to the asker company
    - ADMIN can transition: ACTIVE -> SUSPENDED, WITHDRAWN -> SUSPENDED, SUSPENDED -> ACTIVE
    - Company members can transition: ACTIVE -> WITHDRAWN
    - Updates to price/validity only allowed when status is ACTIVE
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List

from app import schemas
from app.enums import AskStatus, ListingStatus, UserRole
from app.exceptions import (
    ForbiddenException,
    InsufficientPermissionsException,
    WasNotFoundException,
)
from app.repositories import AskRepository, ListingRepository
from app.schemas.base import MonetaID

logger = logging.getLogger(__name__)


# Status transition rules
# Company users (asker company with UPDATE.INSTRUMENT permission): ACTIVE -> WITHDRAWN only
COMPANY_ALLOWED_TRANSITIONS: Dict[AskStatus, List[AskStatus]] = {
    AskStatus.ACTIVE: [AskStatus.WITHDRAWN],
}

# Admin allowed transitions: ACTIVE -> SUSPENDED, WITHDRAWN -> SUSPENDED, SUSPENDED -> ACTIVE
ADMIN_ALLOWED_TRANSITIONS: Dict[AskStatus, List[AskStatus]] = {
    AskStatus.ACTIVE: [AskStatus.SUSPENDED],
    AskStatus.WITHDRAWN: [AskStatus.SUSPENDED],
    AskStatus.SUSPENDED: [AskStatus.ACTIVE],
}


async def validate_listing_is_open(
    listing_repo: ListingRepository,
    listing_id: MonetaID,
) -> schemas.Listing:
    """
    Validate that a listing exists and is in OPEN status.

    Args:
        listing_repo: The Listing repository instance.
        listing_id: The ID of the listing.

    Returns:
        The listing if it exists and is OPEN.

    Raises:
        WasNotFoundException: If listing doesn't exist.
        ForbiddenException: If listing is not OPEN.
    """
    listing = await listing_repo.get_by_id(listing_id)
    if not listing:
        raise WasNotFoundException(
            detail=f'Listing with ID {listing_id} does not exist'
        )

    if listing.status != ListingStatus.OPEN:
        raise ForbiddenException(
            detail=f'Listing is not open (status: {listing.status.value})'
        )

    return listing


def validate_valid_until(valid_until: datetime | None) -> None:
    """
    Validate that valid_until is in the future if provided.

    Args:
        valid_until: The validity timestamp to check.

    Raises:
        ForbiddenException: If valid_until is in the past.
    """
    if valid_until is not None:
        now = datetime.now(timezone.utc)
        if valid_until <= now:
            raise ForbiddenException(detail='valid_until must be in the future')


def validate_amount(amount: float) -> None:
    """
    Validate that amount is positive.

    Args:
        amount: The amount to check.

    Raises:
        ForbiddenException: If amount is not positive.
    """
    if amount <= 0:
        raise ForbiddenException(detail='Amount must be greater than zero')


async def transition_ask_status(
    ask_repo: AskRepository,
    listing_repo: ListingRepository,
    ask_id: MonetaID,
    new_status: AskStatus,
    user_id: MonetaID,
    user_role: UserRole,
    user_company_id: MonetaID,
) -> schemas.Ask:
    """
    Transition an ask to a new status with proper validation.

    This handles the standard status transitions:
    - Company users (asker company): ACTIVE -> WITHDRAWN only
    - Admin: ACTIVE -> SUSPENDED, WITHDRAWN -> SUSPENDED, SUSPENDED -> ACTIVE

    Args:
        ask_repo: The Ask repository instance.
        listing_repo: The Listing repository instance.
        ask_id: The ID of the ask to transition.
        new_status: The new status to transition to.
        user_id: The ID of the user performing the transition.
        user_role: The role of the user.
        user_company_id: The company ID of the user.

    Returns:
        The updated ask.

    Raises:
        WasNotFoundException: If ask doesn't exist.
        ForbiddenException: If listing is not OPEN or user lacks permission.
        InsufficientPermissionsException: If transition is not allowed.
    """
    logger.debug(
        '[BUSINESS] Ask status transition | ask_id=%s | new_status=%s | '
        'user_id=%s | role=%s',
        ask_id,
        new_status,
        user_id,
        user_role,
    )

    # Get the ask
    ask = await ask_repo.get_by_id(ask_id)
    if not ask:
        logger.warning('[BUSINESS] Ask not found | ask_id=%s', ask_id)
        raise WasNotFoundException(
            detail=f'Ask with ID {ask_id} does not exist'
        )

    current_status = ask.status

    # Same status - no change needed
    if current_status == new_status:
        return ask

    # Validate listing is OPEN
    await validate_listing_is_open(listing_repo, ask.listing_id)

    is_admin = user_role == UserRole.ADMIN
    is_asker_company = ask.asker_company_id == user_company_id

    if is_admin:
        # Admin can only do specific transitions
        allowed = ADMIN_ALLOWED_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            logger.warning(
                '[BUSINESS] Invalid admin transition | ask_id=%s | '
                'current_status=%s | new_status=%s',
                ask_id,
                current_status,
                new_status,
            )
            raise InsufficientPermissionsException(
                detail=f'Admin cannot transition from {current_status.value} to {new_status.value}'
            )
    elif is_asker_company:
        # Company user can only do allowed transitions
        allowed = COMPANY_ALLOWED_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            logger.warning(
                '[BUSINESS] Invalid company user transition | ask_id=%s | '
                'current_status=%s | new_status=%s',
                ask_id,
                current_status,
                new_status,
            )
            raise InsufficientPermissionsException(
                detail=f'Cannot transition from {current_status.value} to {new_status.value}'
            )
    else:
        # User is not from asker company and is not admin
        logger.warning(
            '[BUSINESS] Unauthorized ask update | ask_id=%s | '
            'asker_company_id=%s | user_company_id=%s',
            ask_id,
            ask.asker_company_id,
            user_company_id,
        )
        raise ForbiddenException(
            detail='You do not have permission to update this ask'
        )

    # Perform the update
    updated = await ask_repo.update_status(ask_id, new_status)

    logger.info(
        '[BUSINESS] Ask status transitioned | ask_id=%s | '
        'old_status=%s | new_status=%s | transitioned_by=%s',
        ask_id,
        current_status,
        new_status,
        user_id,
    )
    return updated


async def update_ask(
    ask_repo: AskRepository,
    listing_repo: ListingRepository,
    ask_id: MonetaID,
    update_data: schemas.AskUpdate,
    user_id: MonetaID,
    user_company_id: MonetaID,
) -> schemas.Ask:
    """
    Update an ask's price or validity.

    Only allowed if:
    - Ask status is ACTIVE
    - Listing status is OPEN
    - User is from the asker company

    Args:
        ask_repo: The Ask repository instance.
        listing_repo: The Listing repository instance.
        ask_id: The ID of the ask to update.
        update_data: The update data.
        user_id: The ID of the user performing the update.
        user_company_id: The company ID of the user.

    Returns:
        The updated ask.

    Raises:
        WasNotFoundException: If ask doesn't exist.
        ForbiddenException: If ask is not ACTIVE, listing is not OPEN,
            or user lacks permission.
    """
    logger.debug(
        '[BUSINESS] Updating ask | ask_id=%s | user_id=%s | update_data=%s',
        ask_id,
        user_id,
        update_data.model_dump(exclude_none=True),
    )

    # Get the ask
    ask = await ask_repo.get_by_id(ask_id)
    if not ask:
        logger.warning('[BUSINESS] Ask not found | ask_id=%s', ask_id)
        raise WasNotFoundException(
            detail=f'Ask with ID {ask_id} does not exist'
        )

    # Check ask status is ACTIVE
    if ask.status != AskStatus.ACTIVE:
        logger.warning(
            '[BUSINESS] Cannot update non-ACTIVE ask | ask_id=%s | status=%s',
            ask_id,
            ask.status,
        )
        raise ForbiddenException(
            detail=f'Cannot update ask in {ask.status.value} status. Only ACTIVE asks can be updated.'
        )

    # Validate listing is OPEN
    await validate_listing_is_open(listing_repo, ask.listing_id)

    # Validate user is from the asker company
    if ask.asker_company_id != user_company_id:
        logger.warning(
            '[BUSINESS] User company does not own ask | '
            'ask_id=%s | asker_company_id=%s | user_company_id=%s',
            ask_id,
            ask.asker_company_id,
            user_company_id,
        )
        raise ForbiddenException(
            detail='Only the asker company can update this ask'
        )

    # Validate update data
    if update_data.amount is not None:
        validate_amount(update_data.amount)
    if update_data.valid_until is not None:
        validate_valid_until(update_data.valid_until)

    # Perform the update
    updated = await ask_repo.update_by_id(ask_id, update_data)
    if not updated:
        logger.error('[BUSINESS] Failed to update ask | ask_id=%s', ask_id)
        raise WasNotFoundException(
            detail=f'Ask with ID {ask_id} does not exist'
        )

    logger.info(
        '[BUSINESS] Ask updated | ask_id=%s | updated_by=%s | changes=%s',
        ask_id,
        user_id,
        update_data.model_dump(exclude_none=True),
    )
    return updated
