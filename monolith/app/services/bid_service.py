"""
Bid Service.

This module contains service functions for managing bid status transitions.
It centralizes all business logic for bid status changes to ensure proper
validation and consistency.

Key rules:
    - Bids can only be created/updated when the listing is OPEN
    - ADMIN can transition: PENDING -> SUSPENDED, WITHDRAWN -> SUSPENDED
    - Company members (bidder company) can transition: PENDING -> WITHDRAWN
    - Accept bid: PENDING -> SELECTED (sets other PENDING bids to NOT_SELECTED)
    - Reject bid: PENDING -> NOT_SELECTED
"""

import logging
from typing import Dict, List

from app import schemas
from app.enums import BidStatus, ListingStatus, UserRole
from app.exceptions import (
    ForbiddenException,
    InsufficientPermissionsException,
    WasNotFoundException,
)
from app.repositories import BidRepository, ListingRepository
from app.schemas.base import MonetaID

logger = logging.getLogger(__name__)


# Status transition rules
# Company users (bidder company with UPDATE.INSTRUMENT permission): PENDING -> WITHDRAWN only
COMPANY_ALLOWED_TRANSITIONS: Dict[BidStatus, List[BidStatus]] = {
    BidStatus.PENDING: [BidStatus.WITHDRAWN],
}

# Admin allowed transitions: PENDING -> SUSPENDED, WITHDRAWN -> SUSPENDED
ADMIN_ALLOWED_TRANSITIONS: Dict[BidStatus, List[BidStatus]] = {
    BidStatus.PENDING: [BidStatus.SUSPENDED],
    BidStatus.WITHDRAWN: [BidStatus.SUSPENDED],
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
            detail=f'Listing is not open for bidding (status: {listing.status.value})'
        )

    return listing


async def transition_bid_status(
    bid_repo: BidRepository,
    listing_repo: ListingRepository,
    bid_id: MonetaID,
    new_status: BidStatus,
    user_id: MonetaID,
    user_role: UserRole,
    user_company_id: MonetaID,
) -> schemas.Bid:
    """
    Transition a bid to a new status with proper validation.

    This handles the standard status transitions:
    - Company users (bidder company): PENDING -> WITHDRAWN only
    - Admin: PENDING -> SUSPENDED, WITHDRAWN -> SUSPENDED

    Args:
        bid_repo: The Bid repository instance.
        listing_repo: The Listing repository instance.
        bid_id: The ID of the bid to transition.
        new_status: The new status to transition to.
        user_id: The ID of the user performing the transition.
        user_role: The role of the user.
        user_company_id: The company ID of the user.

    Returns:
        The updated bid.

    Raises:
        WasNotFoundException: If bid doesn't exist.
        ForbiddenException: If listing is not OPEN or user lacks permission.
        InsufficientPermissionsException: If transition is not allowed.
    """
    logger.debug(
        '[BUSINESS] Bid status transition | bid_id=%s | new_status=%s | '
        'user_id=%s | role=%s',
        bid_id,
        new_status,
        user_id,
        user_role,
    )

    # Get the bid
    bid = await bid_repo.get_by_id(bid_id)
    if not bid:
        logger.warning('[BUSINESS] Bid not found | bid_id=%s', bid_id)
        raise WasNotFoundException(
            detail=f'Bid with ID {bid_id} does not exist'
        )

    current_status = bid.status

    # Same status - no change needed
    if current_status == new_status:
        return bid

    # Validate listing is OPEN
    await validate_listing_is_open(listing_repo, bid.listing_id)

    is_admin = user_role == UserRole.ADMIN
    is_bidder_company = bid.bidder_company_id == user_company_id

    if is_admin:
        # Admin can only do specific transitions
        allowed = ADMIN_ALLOWED_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            logger.warning(
                '[BUSINESS] Invalid admin transition | bid_id=%s | '
                'current_status=%s | new_status=%s',
                bid_id,
                current_status,
                new_status,
            )
            raise InsufficientPermissionsException(
                detail=f'Admin cannot transition from {current_status.value} to {new_status.value}'
            )
    elif is_bidder_company:
        # Company user can only do allowed transitions
        allowed = COMPANY_ALLOWED_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            logger.warning(
                '[BUSINESS] Invalid company user transition | bid_id=%s | '
                'current_status=%s | new_status=%s',
                bid_id,
                current_status,
                new_status,
            )
            raise InsufficientPermissionsException(
                detail=f'Cannot transition from {current_status.value} to {new_status.value}'
            )
    else:
        # User is not from bidder company and is not admin
        logger.warning(
            '[BUSINESS] Unauthorized bid update | bid_id=%s | '
            'bidder_company_id=%s | user_company_id=%s',
            bid_id,
            bid.bidder_company_id,
            user_company_id,
        )
        raise ForbiddenException(
            detail='You do not have permission to update this bid'
        )

    # Perform the update
    updated = await bid_repo.update_status(bid_id, new_status)

    logger.info(
        '[BUSINESS] Bid status transitioned | bid_id=%s | '
        'old_status=%s | new_status=%s | transitioned_by=%s',
        bid_id,
        current_status,
        new_status,
        user_id,
    )
    return updated


async def accept_bid(
    bid_repo: BidRepository,
    listing_repo: ListingRepository,
    bid_id: MonetaID,
    user_id: MonetaID,
    user_company_id: MonetaID,
) -> schemas.Bid:
    """
    Accept a bid on a listing.

    This transitions the bid from PENDING to SELECTED and sets all other
    PENDING bids for the same listing to NOT_SELECTED.

    Can only be done by a user from the company that owns the listing.

    Args:
        bid_repo: The Bid repository instance.
        listing_repo: The Listing repository instance.
        bid_id: The ID of the bid to accept.
        user_id: The ID of the user accepting the bid.
        user_company_id: The company ID of the user.

    Returns:
        The accepted bid.

    Raises:
        WasNotFoundException: If bid or listing doesn't exist.
        ForbiddenException: If listing is not OPEN or user lacks permission.
        InsufficientPermissionsException: If bid is not in PENDING status.
    """
    logger.debug(
        '[BUSINESS] Accepting bid | bid_id=%s | user_id=%s | user_company_id=%s',
        bid_id,
        user_id,
        user_company_id,
    )

    # Get the bid
    bid = await bid_repo.get_by_id(bid_id)
    if not bid:
        logger.warning('[BUSINESS] Bid not found | bid_id=%s', bid_id)
        raise WasNotFoundException(
            detail=f'Bid with ID {bid_id} does not exist'
        )

    # Validate bid is in PENDING status
    if bid.status != BidStatus.PENDING:
        logger.warning(
            '[BUSINESS] Cannot accept non-PENDING bid | bid_id=%s | status=%s',
            bid_id,
            bid.status,
        )
        raise InsufficientPermissionsException(
            detail=f'Cannot accept bid in {bid.status.value} status. Only PENDING bids can be accepted.'
        )

    # Get the listing and validate it's OPEN
    listing = await validate_listing_is_open(listing_repo, bid.listing_id)

    # Validate user is from the seller company
    if listing.seller_company_id != user_company_id:
        logger.warning(
            '[BUSINESS] User company does not own listing | '
            'listing_id=%s | seller_company_id=%s | user_company_id=%s',
            bid.listing_id,
            listing.seller_company_id,
            user_company_id,
        )
        raise ForbiddenException(
            detail='Only the listing owner can accept bids'
        )

    # Set all other PENDING bids to NOT_SELECTED
    other_pending_bids = await bid_repo.get_pending_bids_for_listing_except(
        bid.listing_id, bid_id
    )
    for other_bid in other_pending_bids:
        await bid_repo.update_status(other_bid.id, BidStatus.NOT_SELECTED)
        logger.debug(
            '[BUSINESS] Set bid to NOT_SELECTED | bid_id=%s',
            other_bid.id,
        )

    # Accept the bid
    accepted_bid = await bid_repo.update_status(bid_id, BidStatus.SELECTED)

    logger.info(
        '[BUSINESS] Bid accepted | bid_id=%s | listing_id=%s | '
        'accepted_by=%s | rejected_bids=%d',
        bid_id,
        bid.listing_id,
        user_id,
        len(other_pending_bids),
    )
    return accepted_bid


async def reject_bid(
    bid_repo: BidRepository,
    listing_repo: ListingRepository,
    bid_id: MonetaID,
    user_id: MonetaID,
    user_company_id: MonetaID,
) -> schemas.Bid:
    """
    Reject a bid on a listing.

    This transitions the bid from PENDING to NOT_SELECTED.

    Can only be done by a user from the company that owns the listing.

    Args:
        bid_repo: The Bid repository instance.
        listing_repo: The Listing repository instance.
        bid_id: The ID of the bid to reject.
        user_id: The ID of the user rejecting the bid.
        user_company_id: The company ID of the user.

    Returns:
        The rejected bid.

    Raises:
        WasNotFoundException: If bid or listing doesn't exist.
        ForbiddenException: If listing is not OPEN or user lacks permission.
        InsufficientPermissionsException: If bid is not in PENDING status.
    """
    logger.debug(
        '[BUSINESS] Rejecting bid | bid_id=%s | user_id=%s | user_company_id=%s',
        bid_id,
        user_id,
        user_company_id,
    )

    # Get the bid
    bid = await bid_repo.get_by_id(bid_id)
    if not bid:
        logger.warning('[BUSINESS] Bid not found | bid_id=%s', bid_id)
        raise WasNotFoundException(
            detail=f'Bid with ID {bid_id} does not exist'
        )

    # Validate bid is in PENDING status
    if bid.status != BidStatus.PENDING:
        logger.warning(
            '[BUSINESS] Cannot reject non-PENDING bid | bid_id=%s | status=%s',
            bid_id,
            bid.status,
        )
        raise InsufficientPermissionsException(
            detail=f'Cannot reject bid in {bid.status.value} status. Only PENDING bids can be rejected.'
        )

    # Get the listing and validate it's OPEN
    listing = await validate_listing_is_open(listing_repo, bid.listing_id)

    # Validate user is from the seller company
    if listing.seller_company_id != user_company_id:
        logger.warning(
            '[BUSINESS] User company does not own listing | '
            'listing_id=%s | seller_company_id=%s | user_company_id=%s',
            bid.listing_id,
            listing.seller_company_id,
            user_company_id,
        )
        raise ForbiddenException(
            detail='Only the listing owner can reject bids'
        )

    # Reject the bid
    rejected_bid = await bid_repo.update_status(bid_id, BidStatus.NOT_SELECTED)

    logger.info(
        '[BUSINESS] Bid rejected | bid_id=%s | listing_id=%s | rejected_by=%s',
        bid_id,
        bid.listing_id,
        user_id,
    )
    return rejected_bid
