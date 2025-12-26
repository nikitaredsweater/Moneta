"""
Contains filtering functions for listing entities.
"""

from typing import Optional

from app import models, schemas
from sqlalchemy import asc, desc

ALLOWED_SORT_COLUMNS = {
    "created_at": models.Listing.created_at,
    "status": models.Listing.status,
}


def build_sort_listing(sort_expr: Optional[str]):
    """
    Convert e.g. "-created_at,status" into [desc(Model.created_at), asc(Model.status)]
    Only whitelisted fields are allowed.
    """
    if not sort_expr:
        return []
    orders = []
    for token in (sort_expr or "").split(","):
        token = token.strip()
        if not token:
            continue
        is_desc = token.startswith("-")
        key = token[1:] if is_desc else token
        col = ALLOWED_SORT_COLUMNS.get(key)
        if not col:
            # ignore unknown columns silently
            continue
        orders.append(desc(col) if is_desc else asc(col))
    return orders


def build_where_listing(filters: schemas.ListingFilters) -> list:
    """
    Constructs a where array, passable to listing repository.

    Args:
        filters (schemas.ListingFilters): incoming filters

    Returns:
        list of correctly configured search params
    """
    M = models.Listing
    where = []

    # Exact status match
    if filters.status is not None:
        where.append(M.status == filters.status)

    # Arrays (IN filters)
    if filters.instrument_id:
        where.append(M.instrument_id.in_(filters.instrument_id))
    if filters.seller_company_id:
        where.append(M.seller_company_id.in_(filters.seller_company_id))
    if filters.listing_creator_user_id:
        where.append(M.listing_creator_user_id.in_(filters.listing_creator_user_id))

    return where
