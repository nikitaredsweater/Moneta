"""
Contains all filtering functions for all possible entities
"""
# TODO: In the future split them into separate files?
from typing import List, Optional

from sqlalchemy import and_, or_, asc, desc
from app import models, schemas

ALLOWED_SORT_COLUMNS = {
    "created_at": models.Instrument.created_at,
    "maturity_date": models.Instrument.maturity_date,
    "face_value": models.Instrument.face_value,
    "maturity_payment": models.Instrument.maturity_payment,
    "name": models.Instrument.name,
}

def build_sort_instrument(sort_expr: Optional[str]):
    """
    Convert e.g. "-created_at,name" into [desc(Model.created_at), asc(Model.name)]
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
            # ignore unknown columns silently (or raise if you prefer)
            continue
        orders.append(desc(col) if is_desc else asc(col))
    return orders


def build_where_instrument(filters: schemas.InstrumentFilters) -> list:
    """
    constructs a where array, passable to instrument repository

    Args:
        filters (schemas.InstrumentFilters): incomming filters
    
    Returns:
        list of correclty configured search params
    """
    M = models.Instrument
    where = []

    # # Numeric ranges
    if filters.min_face_value is not None:
        where.append(M.face_value >= filters.min_face_value)
    if filters.max_face_value is not None:
        where.append(M.face_value <= filters.max_face_value)

    if filters.min_maturity_payment is not None:
        where.append(M.maturity_payment >= filters.min_maturity_payment)
    if filters.max_maturity_payment is not None:
        where.append(M.maturity_payment <= filters.max_maturity_payment)

    # Exact matches
    if filters.currency:
        where.append(M.currency == filters.currency)
    if filters.instrument_status is not None:
        where.append(M.instrument_status == filters.instrument_status)
    if filters.maturity_status is not None:
        where.append(M.maturity_status == filters.maturity_status)

    # Date ranges
    if filters.maturity_date_after:
        where.append(M.maturity_date >= filters.maturity_date_after)
    if filters.maturity_date_before:
        where.append(M.maturity_date <= filters.maturity_date_before)
    if filters.created_at_after:
        where.append(M.created_at >= filters.created_at_after)
    if filters.created_at_before:
        where.append(M.created_at <= filters.created_at_before)

    # Arrays (IN filters)
    if filters.issuer_id:
        where.append(M.issuer_id.in_(filters.issuer_id))
    if filters.created_by:
        where.append(M.created_by.in_(filters.created_by))

    return where