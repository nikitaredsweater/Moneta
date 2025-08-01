"""
Company address endpoints
"""

from typing import List, Optional

from app import repositories as repo
from app import schemas
from fastapi import APIRouter

company_address_router = APIRouter()


@company_address_router.get('/', response_model=List[schemas.CompanyAddress])
async def get_companies(
    company_repo: repo.CompanyAddress,
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
async def create_company(
    company_data: schemas.CompanyAddressCreate,
    company_repo: repo.CompanyAddress,
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
