"""
Company address endpoints
"""

from typing import List, Optional

from fastapi import APIRouter, Depends

from app import repositories as repo
from app import schemas
from app.enums import PermissionEntity as Entity
from app.enums import PermissionVerb as Verb
from app.security import Permission, has_permission

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
    Create a new user

    Args:
        company_data: Company creation data
        company_repo: Company repository dependency

    Returns:
        Company: The created user object
    """
    company = await company_repo.create(company_data)
    return company