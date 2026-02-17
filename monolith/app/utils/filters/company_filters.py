from typing import Optional

from app import models, schemas
from sqlalchemy import asc, desc

ALLOWED_SORT_COLUMNS_COMPANY = {
    'created_at': models.Company.created_at,
    'legal_name': models.Company.legal_name,
    'trade_name': models.Company.trade_name,
    'registration_number': models.Company.registration_number,
    'incorporation_date': models.Company.incorporation_date,
}


def build_sort_company(sort_expr: Optional[str]):
    if not sort_expr:
        return []
    orders = []
    for token in (sort_expr or '').split(','):
        token = token.strip()
        if not token:
            continue
        is_desc = token.startswith('-')
        key = token[1:] if is_desc else token
        col = ALLOWED_SORT_COLUMNS_COMPANY.get(key)
        if not col:
            continue
        orders.append(desc(col) if is_desc else asc(col))
    return orders


def build_where_company(filters: schemas.CompanyFilters) -> list:
    C = models.Company
    w = []

    # partial (ILIKE) matches
    if filters.legal_name:
        w.append(C.legal_name.ilike(f'%{filters.legal_name}%'))
    if filters.trade_name:
        w.append(C.trade_name.ilike(f'%{filters.trade_name}%'))
    if filters.registration_number:
        w.append(
            C.registration_number.ilike(f'%{filters.registration_number}%')
        )

    # date ranges
    if filters.incorporation_date_after:
        w.append(C.incorporation_date >= filters.incorporation_date_after)
    if filters.incorporation_date_before:
        w.append(C.incorporation_date <= filters.incorporation_date_before)
    if filters.created_at_after:
        w.append(C.created_at >= filters.created_at_after)
    if filters.created_at_before:
        w.append(C.created_at <= filters.created_at_before)

    return w
