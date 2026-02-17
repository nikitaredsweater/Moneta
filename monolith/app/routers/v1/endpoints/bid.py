"""
Bid endpoints
"""

import logging
from typing import List, Set

from app import repositories as repo
from app import schemas
from app.dependencies import get_current_user, parse_bid_includes
from app.enums import BidInclude, ListingStatus, UserRole
from app.enums import PermissionEntity as Entity
from app.enums import PermissionVerb as Verb
from app.exceptions import (
    EntityAlreadyExistsException,
    FailedToCreateEntityException,
    ForbiddenException,
    InsufficientPermissionsException,
    WasNotFoundException,
)
from app.security import Permission, has_permission
from app.services import bid_service
from app.utils.filters.bid_filters import build_sort_bid, build_where_bid
from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)
bid_router = APIRouter()


def map_bid_includes_to_rel_names(includes: Set[BidInclude]) -> List[str]:
    """
    Map include enums to actual relationship attribute names on models.Bid.
    """
    rel_map = {
        BidInclude.LISTING: 'listing',
    }
    return [rel_map[i] for i in includes if i in rel_map]


@bid_router.post('/search', response_model=List[schemas.BidWithListing])
async def search_bids(
    bid_repo: repo.Bid,
    filters: schemas.BidFilters,
    includes: Set[BidInclude] = Depends(parse_bid_includes),
    _=Depends(has_permission([Permission(Verb.VIEW, Entity.INSTRUMENT)])),
) -> List[schemas.BidWithListing]:
    """
    Search bids based on filter parameters.

    Args:
        bid_repo: Bid repository dependency.
        filters: Search filters.
        includes: Optional related entities to include.

    Returns:
        List of bids matching the filters.
    """
    logger.debug(
        '[BUSINESS] Searching bids | limit=%d | offset=%d | includes=%s',
        filters.limit,
        filters.offset,
        list(includes) if includes else [],
    )

    where = build_where_bid(filters)
    order_list = build_sort_bid(filters.sort)
    rel_names = map_bid_includes_to_rel_names(includes)

    if rel_names:
        bids = await bid_repo.get_all(
            where_list=where or None,
            order_list=order_list or None,
            limit=filters.limit,
            offset=filters.offset,
            includes=rel_names,
            custom_model=schemas.BidWithListing,
        )
    else:
        bids = await bid_repo.get_all(
            where_list=where or None,
            order_list=order_list or None,
            limit=filters.limit,
            offset=filters.offset,
        )
        # Convert to BidWithListing for consistent response type
        bids = [schemas.BidWithListing(**b.model_dump()) for b in bids]

    logger.info('[BUSINESS] Bid search completed | results=%d', len(bids))
    return bids


@bid_router.get('/{bid_id}', response_model=schemas.BidWithListing)
async def get_bid(
    bid_id: schemas.MonetaID,
    bid_repo: repo.Bid,
    includes: Set[BidInclude] = Depends(parse_bid_includes),
    _=Depends(has_permission([Permission(Verb.VIEW, Entity.INSTRUMENT)])),
) -> schemas.BidWithListing:
    """
    Get bid by its id.

    Args:
        bid_id: The bid UUID.
        bid_repo: Bid repository dependency.
        includes: Optional related entities to include.

    Returns:
        The bid with optional includes.
    """
    logger.debug(
        '[BUSINESS] Fetching bid | bid_id=%s | includes=%s',
        bid_id,
        list(includes) if includes else [],
    )

    rel_names = map_bid_includes_to_rel_names(includes)

    if rel_names:
        bid = await bid_repo.get_by_id(
            pk=bid_id,
            includes=rel_names,
            custom_model=schemas.BidWithListing,
        )
    else:
        base = await bid_repo.get_by_id(pk=bid_id)
        if base:
            bid = schemas.BidWithListing(**base.model_dump())
        else:
            bid = None

    if not bid:
        logger.warning('[BUSINESS] Bid not found | bid_id=%s', bid_id)
        raise WasNotFoundException(
            detail=f'Bid with ID {bid_id} does not exist'
        )

    logger.info('[BUSINESS] Bid retrieved | bid_id=%s', bid_id)
    return bid


@bid_router.post('/', response_model=schemas.Bid)
async def create_bid(
    bid_data: schemas.BidCreate,
    bid_repo: repo.Bid,
    listing_repo: repo.Listing,
    current_user=Depends(get_current_user),
    _=Depends(has_permission([Permission(Verb.UPDATE, Entity.INSTRUMENT)])),
) -> schemas.Bid:
    """
    Create a new bid on a listing.

    Requirements:
    - The listing must be in OPEN status
    - User's company cannot be the seller (no self-bidding)
    - One company can make multiple bids on the same listing

    Args:
        bid_data: Bid creation data.
        bid_repo: Bid repository dependency.
        listing_repo: Listing repository dependency.
        current_user: The authenticated user.

    Returns:
        The created bid.

    Raises:
        WasNotFoundException: If listing doesn't exist.
        ForbiddenException: If listing is not OPEN or user tries to self-bid.
    """
    logger.debug(
        '[BUSINESS] Creating bid | listing_id=%s | user_id=%s | company_id=%s | amount=%s %s',
        bid_data.listing_id,
        current_user.id,
        current_user.company_id,
        bid_data.amount,
        bid_data.currency,
    )

    # Check that the listing exists
    listing = await listing_repo.get_by_id(bid_data.listing_id)
    if not listing:
        logger.warning(
            '[BUSINESS] Listing not found for bid | listing_id=%s',
            bid_data.listing_id,
        )
        raise WasNotFoundException(
            detail=f'Listing with ID {bid_data.listing_id} does not exist'
        )

    # Check that the listing is OPEN
    if listing.status != ListingStatus.OPEN:
        logger.warning(
            '[BUSINESS] Listing not open for bidding | listing_id=%s | status=%s',
            bid_data.listing_id,
            listing.status,
        )
        raise ForbiddenException(
            detail=f'Listing is not open for bidding (status: {listing.status.value})'
        )

    # Check that bidder is not the seller (no self-bidding)
    if listing.seller_company_id == current_user.company_id:
        logger.warning(
            '[BUSINESS] Self-bidding attempt | listing_id=%s | company_id=%s',
            bid_data.listing_id,
            current_user.company_id,
        )
        raise ForbiddenException(
            detail='You cannot bid on your own listing'
        )

    # Create the bid
    internal_data = schemas.BidCreateInternal(
        listing_id=bid_data.listing_id,
        bidder_company_id=current_user.company_id,
        bidder_user_id=current_user.id,
        amount=bid_data.amount,
        currency=bid_data.currency,
        valid_until=bid_data.valid_until,
    )

    bid = await bid_repo.create(internal_data)
    if not bid:
        logger.error(
            '[BUSINESS] Failed to create bid | listing_id=%s',
            bid_data.listing_id,
        )
        raise FailedToCreateEntityException(detail='Failed to create bid')

    logger.info(
        '[BUSINESS] Bid created | bid_id=%s | listing_id=%s | '
        'bidder_company_id=%s | amount=%s %s',
        bid.id,
        bid.listing_id,
        bid.bidder_company_id,
        bid.amount,
        bid.currency,
    )
    return bid


@bid_router.post('/{bid_id}/transition', response_model=schemas.Bid)
async def update_bid_status(
    bid_id: schemas.MonetaID,
    body: schemas.BidStatusUpdate,
    bid_repo: repo.Bid,
    listing_repo: repo.Listing,
    current_user=Depends(get_current_user),
    _=Depends(has_permission([Permission(Verb.UPDATE, Entity.INSTRUMENT)])),
) -> schemas.Bid:
    """
    Update the status of a bid.

    Transition rules:
    - Company users (bidder company): PENDING -> WITHDRAWN only
    - Admin: PENDING -> SUSPENDED, WITHDRAWN -> SUSPENDED

    Args:
        bid_id: The bid UUID.
        body: The new status.
        bid_repo: Bid repository dependency.
        listing_repo: Listing repository dependency.
        current_user: The authenticated user.

    Returns:
        The updated bid.

    Raises:
        WasNotFoundException: If bid doesn't exist.
        ForbiddenException: If listing is not OPEN.
        InsufficientPermissionsException: If transition is not allowed.
    """
    logger.debug(
        '[BUSINESS] Bid status transition | bid_id=%s | new_status=%s | '
        'user_id=%s | role=%s',
        bid_id,
        body.status,
        current_user.id,
        current_user.role,
    )

    return await bid_service.transition_bid_status(
        bid_repo=bid_repo,
        listing_repo=listing_repo,
        bid_id=bid_id,
        new_status=body.status,
        user_id=current_user.id,
        user_role=current_user.role,
        user_company_id=current_user.company_id,
    )


@bid_router.post('/{bid_id}/accept', response_model=schemas.Bid)
async def accept_bid(
    bid_id: schemas.MonetaID,
    bid_repo: repo.Bid,
    listing_repo: repo.Listing,
    current_user=Depends(get_current_user),
    _=Depends(has_permission([Permission(Verb.UPDATE, Entity.INSTRUMENT)])),
) -> schemas.Bid:
    """
    Accept a bid on a listing.

    Can only be done by a user from the company that owns the listing.
    Sets this bid to SELECTED and all other PENDING bids to NOT_SELECTED.

    Args:
        bid_id: The bid UUID.
        bid_repo: Bid repository dependency.
        listing_repo: Listing repository dependency.
        current_user: The authenticated user.

    Returns:
        The accepted bid.

    Raises:
        WasNotFoundException: If bid doesn't exist.
        ForbiddenException: If listing is not OPEN or user lacks permission.
        InsufficientPermissionsException: If bid is not in PENDING status.
    """
    logger.debug(
        '[BUSINESS] Accepting bid | bid_id=%s | user_id=%s',
        bid_id,
        current_user.id,
    )

    return await bid_service.accept_bid(
        bid_repo=bid_repo,
        listing_repo=listing_repo,
        bid_id=bid_id,
        user_id=current_user.id,
        user_company_id=current_user.company_id,
    )


@bid_router.post('/{bid_id}/reject', response_model=schemas.Bid)
async def reject_bid(
    bid_id: schemas.MonetaID,
    bid_repo: repo.Bid,
    listing_repo: repo.Listing,
    current_user=Depends(get_current_user),
    _=Depends(has_permission([Permission(Verb.UPDATE, Entity.INSTRUMENT)])),
) -> schemas.Bid:
    """
    Reject a bid on a listing.

    Can only be done by a user from the company that owns the listing.
    Sets this bid to NOT_SELECTED.

    Args:
        bid_id: The bid UUID.
        bid_repo: Bid repository dependency.
        listing_repo: Listing repository dependency.
        current_user: The authenticated user.

    Returns:
        The rejected bid.

    Raises:
        WasNotFoundException: If bid doesn't exist.
        ForbiddenException: If listing is not OPEN or user lacks permission.
        InsufficientPermissionsException: If bid is not in PENDING status.
    """
    logger.debug(
        '[BUSINESS] Rejecting bid | bid_id=%s | user_id=%s',
        bid_id,
        current_user.id,
    )

    return await bid_service.reject_bid(
        bid_repo=bid_repo,
        listing_repo=listing_repo,
        bid_id=bid_id,
        user_id=current_user.id,
        user_company_id=current_user.company_id,
    )
