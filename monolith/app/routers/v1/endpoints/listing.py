"""
Listing endpoints
"""

import logging
from typing import Dict, List, Optional, Set

from app import repositories as repo
from app import schemas
from app.dependencies import get_current_user, parse_listing_includes
from app.enums import ListingInclude, ListingStatus, UserRole
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
from app.utils.filters.listing_filters import build_sort_listing, build_where_listing
from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)
listing_router = APIRouter()


def map_listing_includes_to_rel_names(includes: Set[ListingInclude]) -> List[str]:
    """
    Map include enums to actual relationship attribute names on models.Listing.
    """
    rel_map = {
        ListingInclude.INSTRUMENT: 'instrument',
    }
    return [rel_map[i] for i in includes if i in rel_map]


@listing_router.post('/search', response_model=List[schemas.ListingWithInstrument])
async def search_listings(
    listing_repo: repo.Listing,
    filters: schemas.ListingFilters,
    includes: Set[ListingInclude] = Depends(parse_listing_includes),
    _=Depends(has_permission([Permission(Verb.VIEW, Entity.INSTRUMENT)])),
) -> List[schemas.ListingWithInstrument]:
    """
    Search listings based on filter parameters.

    Args:
        listing_repo: Listing repository dependency.
        filters: Search filters.
        includes: Optional related entities to include.

    Returns:
        List of listings matching the filters.
    """
    logger.debug(
        '[BUSINESS] Searching listings | limit=%d | offset=%d | includes=%s',
        filters.limit,
        filters.offset,
        list(includes) if includes else [],
    )

    where = build_where_listing(filters)
    order_list = build_sort_listing(filters.sort)
    rel_names = map_listing_includes_to_rel_names(includes)

    if rel_names:
        listings = await listing_repo.get_all(
            where_list=where or None,
            order_list=order_list or None,
            limit=filters.limit,
            offset=filters.offset,
            includes=rel_names,
            custom_model=schemas.ListingWithInstrument,
        )
    else:
        listings = await listing_repo.get_all(
            where_list=where or None,
            order_list=order_list or None,
            limit=filters.limit,
            offset=filters.offset,
        )
        # Convert to ListingWithInstrument for consistent response type
        listings = [
            schemas.ListingWithInstrument(**l.model_dump()) for l in listings
        ]

    logger.info('[BUSINESS] Listing search completed | results=%d', len(listings))
    return listings


@listing_router.get('/{listing_id}', response_model=schemas.ListingWithInstrument)
async def get_listing(
    listing_id: schemas.MonetaID,
    listing_repo: repo.Listing,
    includes: Set[ListingInclude] = Depends(parse_listing_includes),
    _=Depends(has_permission([Permission(Verb.VIEW, Entity.INSTRUMENT)])),
) -> schemas.ListingWithInstrument:
    """
    Get listing by its id.

    Args:
        listing_id: The listing UUID.
        listing_repo: Listing repository dependency.
        includes: Optional related entities to include.

    Returns:
        The listing with optional includes.
    """
    logger.debug(
        '[BUSINESS] Fetching listing | listing_id=%s | includes=%s',
        listing_id,
        list(includes) if includes else [],
    )

    rel_names = map_listing_includes_to_rel_names(includes)

    if rel_names:
        listing = await listing_repo.get_by_id(
            pk=listing_id,
            includes=rel_names,
            custom_model=schemas.ListingWithInstrument,
        )
    else:
        base = await listing_repo.get_by_id(pk=listing_id)
        if base:
            listing = schemas.ListingWithInstrument(**base.model_dump())
        else:
            listing = None

    if not listing:
        logger.warning(
            '[BUSINESS] Listing not found | listing_id=%s', listing_id
        )
        raise WasNotFoundException(
            detail=f'Listing with ID {listing_id} does not exist'
        )

    logger.info('[BUSINESS] Listing retrieved | listing_id=%s', listing_id)
    return listing


@listing_router.post('/', response_model=schemas.Listing)
async def create_listing(
    listing_data: schemas.ListingCreate,
    listing_repo: repo.Listing,
    instrument_repo: repo.Instrument,
    ownership_repo: repo.InstrumentOwnership,
    current_user=Depends(get_current_user),
    _=Depends(has_permission([Permission(Verb.UPDATE, Entity.INSTRUMENT)])),
) -> schemas.Listing:
    """
    Create a new listing for an instrument.

    Requirements:
    - User must be from the company that currently owns the instrument
    - No OPEN listing can already exist for the instrument

    Args:
        listing_data: Listing creation data (only instrument_id required).
        listing_repo: Listing repository dependency.
        instrument_repo: Instrument repository dependency.
        ownership_repo: Ownership repository dependency.
        current_user: The authenticated user.

    Returns:
        The created listing.

    Raises:
        WasNotFoundException: If instrument doesn't exist.
        ForbiddenException: If user's company doesn't own the instrument.
        EntityAlreadyExistsException: If an OPEN listing already exists.
    """
    logger.debug(
        '[BUSINESS] Creating listing | instrument_id=%s | user_id=%s | company_id=%s',
        listing_data.instrument_id,
        current_user.id,
        current_user.company_id,
    )

    # Check that the instrument exists
    instrument = await instrument_repo.get_by_id(listing_data.instrument_id)
    if not instrument:
        logger.warning(
            '[BUSINESS] Instrument not found for listing | instrument_id=%s',
            listing_data.instrument_id,
        )
        raise WasNotFoundException(
            detail=f'Instrument with ID {listing_data.instrument_id} does not exist'
        )

    # Check that the user's company currently owns the instrument
    current_ownership = await ownership_repo.get_current_owner(
        listing_data.instrument_id
    )
    if not current_ownership:
        logger.warning(
            '[BUSINESS] No active ownership for instrument | instrument_id=%s',
            listing_data.instrument_id,
        )
        raise ForbiddenException(
            detail='This instrument has no active owner'
        )

    if current_ownership.owner_id != current_user.company_id:
        logger.warning(
            '[BUSINESS] User company does not own instrument | '
            'instrument_id=%s | owner_id=%s | user_company_id=%s',
            listing_data.instrument_id,
            current_ownership.owner_id,
            current_user.company_id,
        )
        raise ForbiddenException(
            detail='Your company does not own this instrument'
        )

    # Check that no OPEN listing exists for this instrument
    has_open = await listing_repo.has_open_listing(listing_data.instrument_id)
    if has_open:
        logger.warning(
            '[BUSINESS] Open listing already exists | instrument_id=%s',
            listing_data.instrument_id,
        )
        raise EntityAlreadyExistsException(
            detail='An open listing already exists for this instrument'
        )

    # Create the listing
    internal_data = schemas.ListingCreateInternal(
        instrument_id=listing_data.instrument_id,
        seller_company_id=current_user.company_id,
        listing_creator_user_id=current_user.id,
        status=ListingStatus.OPEN,
    )

    listing = await listing_repo.create(internal_data)
    if not listing:
        logger.error(
            '[BUSINESS] Failed to create listing | instrument_id=%s',
            listing_data.instrument_id,
        )
        raise FailedToCreateEntityException(
            detail='Failed to create listing'
        )

    logger.info(
        '[BUSINESS] Listing created | listing_id=%s | instrument_id=%s | '
        'seller_company_id=%s | created_by=%s',
        listing.id,
        listing.instrument_id,
        listing.seller_company_id,
        listing.listing_creator_user_id,
    )
    return listing


# Status transition rules
# Company users (with UPDATE.INSTRUMENT permission): OPEN -> WITHDRAWN only
# Admin: Any transition EXCEPT (OPEN -> WITHDRAWN) and (WITHDRAWN -> OPEN)
COMPANY_ALLOWED_TRANSITIONS: Dict[ListingStatus, List[ListingStatus]] = {
    ListingStatus.OPEN: [ListingStatus.WITHDRAWN],
}

ADMIN_FORBIDDEN_TRANSITIONS: Dict[ListingStatus, List[ListingStatus]] = {
    ListingStatus.OPEN: [ListingStatus.WITHDRAWN],
    ListingStatus.WITHDRAWN: [ListingStatus.OPEN],
}


@listing_router.post(
    '/{listing_id}/transition', response_model=schemas.Listing
)
async def update_listing_status(
    listing_id: schemas.MonetaID,
    body: schemas.ListingStatusUpdate,
    listing_repo: repo.Listing,
    current_user=Depends(get_current_user),
    _=Depends(has_permission([Permission(Verb.UPDATE, Entity.INSTRUMENT)])),
) -> schemas.Listing:
    """
    Update the status of a listing.

    Transition rules:
    - Company users (same company as seller): OPEN -> WITHDRAWN only
    - Admin: Any transition EXCEPT (OPEN -> WITHDRAWN) and (WITHDRAWN -> OPEN)

    Args:
        listing_id: The listing UUID.
        body: The new status.
        listing_repo: Listing repository dependency.
        current_user: The authenticated user.

    Returns:
        The updated listing.

    Raises:
        WasNotFoundException: If listing doesn't exist.
        InsufficientPermissionsException: If transition is not allowed.
    """
    logger.debug(
        '[BUSINESS] Listing status transition | listing_id=%s | '
        'new_status=%s | user_id=%s | role=%s',
        listing_id,
        body.status,
        current_user.id,
        current_user.role,
    )

    listing = await listing_repo.get_by_id(listing_id)
    if not listing:
        logger.warning(
            '[BUSINESS] Listing not found for transition | listing_id=%s',
            listing_id,
        )
        raise WasNotFoundException(
            detail=f'Listing with ID {listing_id} does not exist'
        )

    current_status = listing.status
    new_status = body.status

    # Same status - no change needed
    if current_status == new_status:
        return listing

    is_admin = current_user.role == UserRole.ADMIN
    is_same_company = listing.seller_company_id == current_user.company_id

    if is_admin:
        # Admin can do any transition except the forbidden ones
        forbidden = ADMIN_FORBIDDEN_TRANSITIONS.get(current_status, [])
        if new_status in forbidden:
            logger.warning(
                '[BUSINESS] Forbidden admin transition | listing_id=%s | '
                'current_status=%s | new_status=%s',
                listing_id,
                current_status,
                new_status,
            )
            raise InsufficientPermissionsException(
                detail=f'Admin cannot transition from {current_status.value} to {new_status.value}'
            )
    elif is_same_company:
        # Company user can only do allowed transitions
        allowed = COMPANY_ALLOWED_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            logger.warning(
                '[BUSINESS] Invalid company user transition | listing_id=%s | '
                'current_status=%s | new_status=%s',
                listing_id,
                current_status,
                new_status,
            )
            raise InsufficientPermissionsException(
                detail=f'Cannot transition from {current_status.value} to {new_status.value}'
            )
    else:
        # User is not from the seller company and is not admin
        logger.warning(
            '[BUSINESS] Unauthorized listing update | listing_id=%s | '
            'seller_company_id=%s | user_company_id=%s',
            listing_id,
            listing.seller_company_id,
            current_user.company_id,
        )
        raise ForbiddenException(
            detail='You do not have permission to update this listing'
        )

    # Perform the update
    updated = await listing_repo.update_by_id(
        listing_id,
        schemas.ListingStatusUpdate(status=new_status),
    )

    logger.info(
        '[BUSINESS] Listing status transitioned | listing_id=%s | '
        'old_status=%s | new_status=%s | transitioned_by=%s',
        listing_id,
        current_status,
        new_status,
        current_user.id,
    )
    return updated
