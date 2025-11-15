"""
Company endpoints
"""

import logging
from typing import List, Optional

from app import repositories as repo
from app import schemas
from app.enums import PermissionEntity as Entity
from app.enums import PermissionVerb as Verb
from app.security import Permission, has_permission
from app.utils.filters.company_filters import (
    build_sort_company,
    build_where_company,
)
from fastapi import APIRouter, Depends

logger = logging.getLogger()


company_router = APIRouter()


@company_router.get('/', response_model=List[schemas.Company])
async def get_companies(
    company_repo: repo.Company,
    _=Depends(has_permission([Permission(Verb.VIEW, Entity.COMPANY)])),
) -> Optional[List[schemas.Company]]:
    """
    Get all companies

    Args:
        company_repo (repo.Company): dependency injection of the User Repository

    Returns:
        List[schemas.Company]: A list of company entities.
    """
    companies = await company_repo.get_all()
    return companies


@company_router.get('/{company_id}', response_model=Optional[schemas.Company])
async def get_company_by_uuid(
    company_id: schemas.MonetaID,
    company_repo: repo.Company,
    _=Depends(has_permission([Permission(Verb.VIEW, Entity.COMPANY)])),
) -> Optional[schemas.Company]:
    """
    Get all companies

    Args:
        company_id (schemas.MonetaID): UUID
        company_repo (repo.Company): dependency injection of the User Repository

    Returns:
        Optional[schemas.Company]: A company object.
    """
    company = None
    try:
        company = await company_repo.get_by_id(company_id)
    except Exception as e:
        logger.error(
            f'Error retrieving a company with uuid {company_id}. Error: {e}'
        )
    finally:
        return company


@company_router.post("/search", response_model=List[schemas.Company])
async def search_companies(
    company_repo: repo.Company,
    filters: schemas.CompanyFilters,
    _=Depends(has_permission([Permission(Verb.VIEW, Entity.COMPANY)])),
) -> Optional[List[schemas.Company]]:
    where = build_where_company(filters)
    order = build_sort_company(filters.sort)
    result = await company_repo.get_all(
        where_list=where or None,
        order_list=order or None,
        limit=filters.limit,
        offset=filters.offset,
    )
    return result


@company_router.post('/', response_model=schemas.Company)
async def create_company(
    company_data: schemas.CompanyCreate,
    company_repo: repo.Company,
    _=Depends(has_permission([Permission(Verb.CREATE, Entity.COMPANY)])),
) -> schemas.Company:
    """
    Create a new user

    Args:
        company_data: Company creation data
        company_repo: Company repository dependency

    Returns:
        Company: The created user object
    """
    company = await company_repo.create(company_data)
    return company
