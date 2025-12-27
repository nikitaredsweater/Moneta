"""
Contains filtering functions for ask entities.
"""

from typing import Optional

from app import models, schemas
from sqlalchemy import asc, desc

ALLOWED_SORT_COLUMNS = {
    "created_at": models.Ask.created_at,
    "status": models.Ask.status,
    "amount": models.Ask.amount,
}


def build_sort_ask(sort_expr: Optional[str]):
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


def build_where_ask(filters: schemas.AskFilters) -> list:
    """
    Constructs a where array, passable to ask repository.

    Args:
        filters (schemas.AskFilters): incoming filters

    Returns:
        list of correctly configured search params
    """
    M = models.Ask
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

    # Exact execution_mode match
    if filters.execution_mode is not None:
        where.append(M.execution_mode == filters.execution_mode)

    # Exact binding match
    if filters.binding is not None:
        where.append(M.binding == filters.binding)

    # Arrays (IN filters)
    if filters.listing_id:
        where.append(M.listing_id.in_(filters.listing_id))
    if filters.asker_company_id:
        where.append(M.asker_company_id.in_(filters.asker_company_id))
    if filters.asker_user_id:
        where.append(M.asker_user_id.in_(filters.asker_user_id))

    return where
