"""
Company address endpoints
"""

import logging
from typing import List, Optional

from sqlalchemy.exc import IntegrityError

from app import repositories as repo
from app import schemas
from app.enums import PermissionEntity as Entity
from app.enums import PermissionVerb as Verb
from app.exceptions import WasNotFoundException
from app.security import Permission, has_permission
from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)
company_address_router = APIRouter()


@company_address_router.get('/', response_model=List[schemas.CompanyAddress])
async def get_company_addresses(
    company_repo: repo.CompanyAddress,
    _=Depends(has_permission([Permission(Verb.VIEW, Entity.COMPANY_ADDRESS)])),
) -> Optional[List[schemas.CompanyAddress]]:
    """
    Get all companies

    Args:
        company_repo (repo.Company): dependency injection of the User Repository

    Returns:
        schemas.Company: A user object.
    """
    companies = await company_repo.get_all()
    return companies


@company_address_router.post('/', response_model=schemas.CompanyAddress)
async def create_company_address(
    company_data: schemas.CompanyAddressCreate,
    company_repo: repo.CompanyAddress,
    _=Depends(
        has_permission([Permission(Verb.CREATE, Entity.COMPANY_ADDRESS)])
    ),
) -> schemas.Company:
    """
    Create a new company address

    Args:
        company_data: Company address creation data
        company_repo: Company address repository dependency

    Returns:
        CompanyAddress: The created company address object
    """
    try:
        company = await company_repo.create(company_data)
        return company
    except IntegrityError as e:
        logger.warning(
            '[BUSINESS] Failed to create company address - FK violation | company_id=%s',
            company_data.company_id,
        )
        raise WasNotFoundException(
            detail=f'Company with ID {company_data.company_id} does not exist'
        )
