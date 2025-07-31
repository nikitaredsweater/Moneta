"""
Company endpoints
"""

from typing import List, Optional

from app import repositories as repo
from app import schemas
from fastapi import APIRouter

company_router = APIRouter()


@company_router.get('/', response_model=List[schemas.Company])
async def get_companies(
    company_repo: repo.Company,
) -> Optional[List[schemas.Company]]:
    """
    Get all companies

    Args:
        company_repo (repo.Company): dependency injection of the User Repository

    Returns:
        schemas.Company: A user object.
    """
    companies = await company_repo.get_all()
    return companies


@company_router.post('/', response_model=schemas.Company)
async def create_company(
    company_data: schemas.CompanyCreate, company_repo: repo.Company
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
