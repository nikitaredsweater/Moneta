"""
Company endpoints
"""

import logging
from typing import List, Optional, Set

from app import repositories as repo
from app import schemas
from app.dependencies import parse_company_includes
from app.enums import CompanyInclude
from app.enums import PermissionEntity as Entity
from app.enums import PermissionVerb as Verb
from app.exceptions import WasNotFoundException
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


def map_includes_to_rel_names(includes: Set[CompanyInclude]) -> List[str]:
    """
    Map include enums to actual relationship attribute names on models.Company.
    """
    rel_map = {
        CompanyInclude.ADDRESSES: "addresses",
        CompanyInclude.USERS: "users",
        CompanyInclude.INSTRUMENTS: "instruments",
    }
    return [rel_map[i] for i in includes if i in rel_map]


@company_router.get("/{company_id}", response_model=schemas.CompanyIncludes)
async def get_company_by_uuid(
    company_id: schemas.MonetaID,
    company_repo: repo.Company,
    includes: Set[CompanyInclude] = Depends(parse_company_includes),
    _=Depends(has_permission([Permission(Verb.VIEW, Entity.COMPANY)])),
) -> schemas.CompanyIncludes:
    logger.info("NEW INCLUDES FEATURE")
    logger.info(includes)

    rel_names = map_includes_to_rel_names(includes)

    if rel_names:
        # We want relations → eager-load & deserialize into extended DTO
        company = await company_repo.get_by_id(
            pk=company_id,
            includes=rel_names,
            custom_model=schemas.CompanyIncludes,
        )
        if not company:
            raise WasNotFoundException

        if "addresses" not in rel_names:
            company.addresses = None
        if "users" not in rel_names:
            company.users = None
        # if "instruments" not in rel_names:
        #     company.instruments = None

        return company

    # No includes → use base DTO (no relationships touched)
    base = await company_repo.get_by_id(pk=company_id)
    if not base:
        raise WasNotFoundException

    # Convert base → extended shape, relations stay None
    return schemas.CompanyIncludes(**base.dict())


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
    Create a new company.

    Args:
        company_data: Company creation data
        company_repo: Company repository dependency

    Returns:
        Company: The created user object
    """
    company = await company_repo.create(company_data)
    return company
