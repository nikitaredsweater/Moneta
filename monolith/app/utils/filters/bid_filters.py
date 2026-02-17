"""
Contains filtering functions for bid entities.
"""

from typing import Optional

from app import models, schemas
from sqlalchemy import asc, desc

ALLOWED_SORT_COLUMNS = {
    "created_at": models.Bid.created_at,
    "status": models.Bid.status,
    "amount": models.Bid.amount,
}


def build_sort_bid(sort_expr: Optional[str]):
    """
    Convert e.g. "-created_at,amount" into [desc(Model.created_at), asc(Model.amount)]
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


def build_where_bid(filters: schemas.BidFilters) -> list:
    """
    Constructs a where array, passable to bid repository.

    Args:
        filters (schemas.BidFilters): incoming filters

    Returns:
        list of correctly configured search params
    """
    M = models.Bid
    where = []

    # Exact status match
    if filters.status is not None:
        where.append(M.status == filters.status)

    # Exact currency match
    if filters.currency is not None:
        where.append(M.currency == filters.currency)

    # Amount range filters
    if filters.min_amount is not None:
        where.append(M.amount >= filters.min_amount)
    if filters.max_amount is not None:
        where.append(M.amount <= filters.max_amount)

    # Arrays (IN filters)
    if filters.listing_id:
        where.append(M.listing_id.in_(filters.listing_id))
    if filters.bidder_company_id:
        where.append(M.bidder_company_id.in_(filters.bidder_company_id))
    if filters.bidder_user_id:
        where.append(M.bidder_user_id.in_(filters.bidder_user_id))

    return where
