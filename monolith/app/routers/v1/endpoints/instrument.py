"""
Instrument endpoints
"""

from typing import List, Optional

from fastapi import APIRouter, Depends

from app import repositories as repo
from app import schemas
from app.dependencies import get_current_user

instrument_router = APIRouter()


@instrument_router.get('/', response_model=List[schemas.Instrument])
async def get_companies(
    instrument_repo: repo.Instrument,
) -> Optional[List[schemas.Instrument]]:
    """
    Get all companies

    Args:
        company_repo (repo.Company): dependency injection of the User Repository

    Returns:
        schemas.Company: A user object.
    """
    instruments = await instrument_repo.get_all()
    return instruments


@instrument_router.post('/', response_model=schemas.InstrumentCreate)
async def create_company(
    instrument_data: schemas.InstrumentCreate,
    instrument_repo: repo.Instrument,
    current_user=Depends(get_current_user)
) -> schemas.Instrument:
    """
    Create a new user

    Args:
        company_data: Company creation data
        company_repo: Company repository dependency

    Returns:
        Company: The created user object
    """
    
    internal_data = schemas.InstrumentCreateInternal(
        **instrument_data.dict(),
        issuer_id=current_user.company_id,
        created_by=current_user.id,
    )
    # print(f"Trvwgjhbknlkerwnjkbhjvghwqhcfgvjwhbekjnlkfrjbhj, {internal_data}")
    instrument = await instrument_repo.create(internal_data)
    print(f"Trvwgjhbknlkerwnjkbhjvghwqhcfgvjwhbekjnlkfrjbhj, {instrument}")
    return instrument
