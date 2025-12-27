"""
Ask endpoints
"""

import logging
from datetime import datetime, timezone
from typing import List, Set

from app import repositories as repo
from app import schemas
from app.dependencies import get_current_user, parse_ask_includes
from app.enums import AskInclude, AskStatus, ListingStatus
from app.enums import PermissionEntity as Entity
from app.enums import PermissionVerb as Verb
from app.enums import UserRole
from app.exceptions import (
    FailedToCreateEntityException,
    ForbiddenException,
    WasNotFoundException,
)
from app.security import Permission, has_permission
from app.services import ask_service
from app.utils.filters.ask_filters import build_sort_ask, build_where_ask
from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)
ask_router = APIRouter()


def map_ask_includes_to_rel_names(includes: Set[AskInclude]) -> List[str]:
    """
    Map include enums to actual relationship attribute names on models.Ask.
    """
    rel_map = {
        AskInclude.LISTING: 'listing',
    }
    return [rel_map[i] for i in includes if i in rel_map]


@ask_router.post('/search', response_model=List[schemas.AskWithListing])
async def search_asks(
    ask_repo: repo.Ask,
    listing_repo: repo.Listing,
    filters: schemas.AskFilters,
    includes: Set[AskInclude] = Depends(parse_ask_includes),
    current_user=Depends(get_current_user),
    _=Depends(has_permission([Permission(Verb.VIEW, Entity.INSTRUMENT)])),
) -> List[schemas.AskWithListing]:
    """
    Search asks based on filter parameters.

    Returns only ACTIVE asks for non-owner users.
    Owners of the listing and ADMINs can view all asks.

    Args:
        ask_repo: Ask repository dependency.
        listing_repo: Listing repository dependency.
        filters: Search filters.
        includes: Optional related entities to include.
        current_user: The authenticated user.

    Returns:
        List of asks matching the filters.
    """
    logger.debug(
        '[BUSINESS] Searching asks | limit=%d | offset=%d | includes=%s',
        filters.limit,
        filters.offset,
        list(includes) if includes else [],
    )

    is_admin = current_user.role == UserRole.ADMIN

    # Build base filters
    where = build_where_ask(filters)

    # If not admin, need to check ownership for each listing or filter by ACTIVE status
    if not is_admin:
        # Get the listings to check ownership
        if filters.listing_id:
            # Check if user owns any of the filtered listings
            owned_listing_ids = []
            for lid in filters.listing_id:
                listing = await listing_repo.get_by_id(lid)
                if (
                    listing
                    and listing.seller_company_id == current_user.company_id
                ):
                    owned_listing_ids.append(lid)

            if owned_listing_ids:
                # User owns some listings - can see all asks for those
                # For other listings, only ACTIVE
                # This is complex, so we'll do a simpler approach:
                # If user owns ALL filtered listings, show all statuses
                # Otherwise, filter to ACTIVE only
                if set(owned_listing_ids) == set(filters.listing_id):
                    pass  # User owns all, no status filter needed
                else:
                    # Add ACTIVE status filter for non-owned listings
                    filters.status = AskStatus.ACTIVE
                    where = build_where_ask(filters)
            else:
                # User doesn't own any of the filtered listings
                filters.status = AskStatus.ACTIVE
                where = build_where_ask(filters)
        else:
            # No listing filter - only show ACTIVE asks unless admin
            filters.status = AskStatus.ACTIVE
            where = build_where_ask(filters)

    order_list = build_sort_ask(filters.sort)
    rel_names = map_ask_includes_to_rel_names(includes)

    if rel_names:
        asks = await ask_repo.get_all(
            where_list=where or None,
            order_list=order_list or None,
            limit=filters.limit,
            offset=filters.offset,
            includes=rel_names,
            custom_model=schemas.AskWithListing,
        )
    else:
        asks = await ask_repo.get_all(
            where_list=where or None,
            order_list=order_list or None,
            limit=filters.limit,
            offset=filters.offset,
        )
        # Convert to AskWithListing for consistent response type
        asks = [schemas.AskWithListing(**a.model_dump()) for a in asks]

    logger.info('[BUSINESS] Ask search completed | results=%d', len(asks))
    return asks


@ask_router.get('/{ask_id}', response_model=schemas.AskWithListing)
async def get_ask(
    ask_id: schemas.MonetaID,
    ask_repo: repo.Ask,
    listing_repo: repo.Listing,
    includes: Set[AskInclude] = Depends(parse_ask_includes),
    current_user=Depends(get_current_user),
    _=Depends(has_permission([Permission(Verb.VIEW, Entity.INSTRUMENT)])),
) -> schemas.AskWithListing:
    """
    Get ask by its id.

    Non-owners can only view ACTIVE asks.
    Owners of the listing and ADMINs can view all asks.

    Args:
        ask_id: The ask UUID.
        ask_repo: Ask repository dependency.
        listing_repo: Listing repository dependency.
        includes: Optional related entities to include.
        current_user: The authenticated user.

    Returns:
        The ask with optional includes.
    """
    logger.debug(
        '[BUSINESS] Fetching ask | ask_id=%s | includes=%s',
        ask_id,
        list(includes) if includes else [],
    )

    rel_names = map_ask_includes_to_rel_names(includes)

    if rel_names:
        ask = await ask_repo.get_by_id(
            pk=ask_id,
            includes=rel_names,
            custom_model=schemas.AskWithListing,
        )
    else:
        base = await ask_repo.get_by_id(pk=ask_id)
        if base:
            ask = schemas.AskWithListing(**base.model_dump())
        else:
            ask = None

    if not ask:
        logger.warning('[BUSINESS] Ask not found | ask_id=%s', ask_id)
        raise WasNotFoundException(
            detail=f'Ask with ID {ask_id} does not exist'
        )

    # Check visibility
    is_admin = current_user.role == UserRole.ADMIN
    if not is_admin:
        listing = await listing_repo.get_by_id(ask.listing_id)
        is_owner = (
            listing and listing.seller_company_id == current_user.company_id
        )
        if not is_owner and ask.status != AskStatus.ACTIVE:
            logger.warning(
                '[BUSINESS] Non-owner trying to view non-ACTIVE ask | ask_id=%s',
                ask_id,
            )
            raise WasNotFoundException(
                detail=f'Ask with ID {ask_id} does not exist'
            )

    logger.info('[BUSINESS] Ask retrieved | ask_id=%s', ask_id)
    return ask


@ask_router.post('/', response_model=schemas.Ask)
async def create_ask(
    ask_data: schemas.AskCreate,
    ask_repo: repo.Ask,
    listing_repo: repo.Listing,
    current_user=Depends(get_current_user),
    _=Depends(has_permission([Permission(Verb.UPDATE, Entity.INSTRUMENT)])),
) -> schemas.Ask:
    """
    Create a new ask on a listing.

    Requirements:
    - The listing must be in OPEN status
    - User's company must be the seller (asker company = listing seller company)
    - valid_until (if provided) must be in the future
    - amount must be > 0

    Args:
        ask_data: Ask creation data.
        ask_repo: Ask repository dependency.
        listing_repo: Listing repository dependency.
        current_user: The authenticated user.

    Returns:
        The created ask.

    Raises:
        WasNotFoundException: If listing doesn't exist.
        ForbiddenException: If listing is not OPEN or user is not from seller company.
    """
    logger.debug(
        '[BUSINESS] Creating ask | listing_id=%s | user_id=%s | company_id=%s | amount=%s %s',
        ask_data.listing_id,
        current_user.id,
        current_user.company_id,
        ask_data.amount,
        ask_data.currency,
    )

    # Check that the listing exists
    listing = await listing_repo.get_by_id(ask_data.listing_id)
    if not listing:
        logger.warning(
            '[BUSINESS] Listing not found for ask | listing_id=%s',
            ask_data.listing_id,
        )
        raise WasNotFoundException(
            detail=f'Listing with ID {ask_data.listing_id} does not exist'
        )

    # Check that the listing is OPEN
    if listing.status != ListingStatus.OPEN:
        logger.warning(
            '[BUSINESS] Listing not open for asks | listing_id=%s | status=%s',
            ask_data.listing_id,
            listing.status,
        )
        raise ForbiddenException(
            detail=f'Listing is not open (status: {listing.status.value})'
        )

    # Check that asker is the seller (asker company must equal listing seller company)
    if listing.seller_company_id != current_user.company_id:
        logger.warning(
            '[BUSINESS] Non-owner attempting to create ask | listing_id=%s | '
            'seller_company_id=%s | user_company_id=%s',
            ask_data.listing_id,
            listing.seller_company_id,
            current_user.company_id,
        )
        raise ForbiddenException(
            detail='Only the listing owner can create asks'
        )

    # Validate amount > 0 (already validated by schema, but double-check)
    if ask_data.amount <= 0:
        raise ForbiddenException(detail='Amount must be greater than zero')

    # Validate valid_until is in the future if provided
    if ask_data.valid_until is not None:
        now = datetime.now(timezone.utc)
        if ask_data.valid_until <= now:
            raise ForbiddenException(detail='valid_until must be in the future')

    # Create the ask
    internal_data = schemas.AskCreateInternal(
        listing_id=ask_data.listing_id,
        asker_company_id=current_user.company_id,
        asker_user_id=current_user.id,
        amount=ask_data.amount,
        currency=ask_data.currency,
        valid_until=ask_data.valid_until,
        execution_mode=ask_data.execution_mode,
        binding=ask_data.binding,
    )

    ask = await ask_repo.create(internal_data)
    if not ask:
        logger.error(
            '[BUSINESS] Failed to create ask | listing_id=%s',
            ask_data.listing_id,
        )
        raise FailedToCreateEntityException(detail='Failed to create ask')

    logger.info(
        '[BUSINESS] Ask created | ask_id=%s | listing_id=%s | '
        'asker_company_id=%s | amount=%s %s',
        ask.id,
        ask.listing_id,
        ask.asker_company_id,
        ask.amount,
        ask.currency,
    )
    return ask


@ask_router.post('/{ask_id}/transition', response_model=schemas.Ask)
async def update_ask_status(
    ask_id: schemas.MonetaID,
    body: schemas.AskStatusUpdate,
    ask_repo: repo.Ask,
    listing_repo: repo.Listing,
    current_user=Depends(get_current_user),
    _=Depends(has_permission([Permission(Verb.UPDATE, Entity.INSTRUMENT)])),
) -> schemas.Ask:
    """
    Update the status of an ask.

    Transition rules:
    - Company users (asker company): ACTIVE -> WITHDRAWN only
    - Admin: ACTIVE -> SUSPENDED, WITHDRAWN -> SUSPENDED, SUSPENDED -> ACTIVE

    Args:
        ask_id: The ask UUID.
        body: The new status.
        ask_repo: Ask repository dependency.
        listing_repo: Listing repository dependency.
        current_user: The authenticated user.

    Returns:
        The updated ask.

    Raises:
        WasNotFoundException: If ask doesn't exist.
        ForbiddenException: If listing is not OPEN.
        InsufficientPermissionsException: If transition is not allowed.
    """
    logger.debug(
        '[BUSINESS] Ask status transition | ask_id=%s | new_status=%s | '
        'user_id=%s | role=%s',
        ask_id,
        body.status,
        current_user.id,
        current_user.role,
    )

    return await ask_service.transition_ask_status(
        ask_repo=ask_repo,
        listing_repo=listing_repo,
        ask_id=ask_id,
        new_status=body.status,
        user_id=current_user.id,
        user_role=current_user.role,
        user_company_id=current_user.company_id,
    )


@ask_router.patch('/{ask_id}', response_model=schemas.Ask)
async def update_ask(
    ask_id: schemas.MonetaID,
    body: schemas.AskUpdate,
    ask_repo: repo.Ask,
    listing_repo: repo.Listing,
    current_user=Depends(get_current_user),
    _=Depends(has_permission([Permission(Verb.UPDATE, Entity.INSTRUMENT)])),
) -> schemas.Ask:
    """
    Update ask price or validity.

    Only allowed if:
    - Ask status is ACTIVE
    - Listing status is OPEN
    - User is from the asker company

    Args:
        ask_id: The ask UUID.
        body: The update data (amount, currency, valid_until).
        ask_repo: Ask repository dependency.
        listing_repo: Listing repository dependency.
        current_user: The authenticated user.

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
        current_user.id,
        body.model_dump(exclude_none=True),
    )

    return await ask_service.update_ask(
        ask_repo=ask_repo,
        listing_repo=listing_repo,
        ask_id=ask_id,
        update_data=body,
        user_id=current_user.id,
        user_company_id=current_user.company_id,
    )
