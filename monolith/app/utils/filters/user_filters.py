from typing import Optional, List
from sqlalchemy import and_, or_, asc, desc
from app import models, schemas

# Whitelist columns for sorting
ALLOWED_SORT_COLUMNS_USER = {
    "created_at": models.User.created_at,
    "email": models.User.email,
    "first_name": models.User.first_name,
    "last_name": models.User.last_name,
    "role": models.User.role,
    "company_id": models.User.company_id,
}

def build_sort_user(sort_expr: Optional[str]):
    """
    Convert e.g. "-created_at,first_name" into
    [desc(User.created_at), asc(User.first_name)]
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
        col = ALLOWED_SORT_COLUMNS_USER.get(key)
        if not col:
            continue
        orders.append(desc(col) if is_desc else asc(col))
    return orders

def build_where_user(filters: schemas.UserFilters) -> list:
    """
    Build SQLAlchemy conditions for Users based on filters.
    - Partial matches for email/first_name/last_name (ILIKE)
    - Exact matches for role/company_id
    - created_at range
    """
    U = models.User
    where = []

    # Partial (case-insensitive) matches
    if filters.email:
        like = f"%{filters.email}%"
        where.append(U.email.ilike(like))
    if filters.first_name:
        like = f"%{filters.first_name}%"
        where.append(U.first_name.ilike(like))
    if filters.last_name:
        like = f"%{filters.last_name}%"
        where.append(U.last_name.ilike(like))

    # Exact filters
    if filters.role is not None:
        where.append(U.role == filters.role)
    if filters.company_id is not None:
        where.append(U.company_id == filters.company_id)

    # Date range (created_at)
    if filters.created_at_after:
        where.append(U.created_at >= filters.created_at_after)
    if filters.created_at_before:
        where.append(U.created_at <= filters.created_at_before)

    return where
