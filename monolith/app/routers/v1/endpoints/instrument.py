"""
Instrument endpoints
"""

from typing import List, Optional

from app import repositories as repo
from app import schemas
from app import models
import logging
from sqlalchemy import and_, or_, asc, desc
from app.dependencies import get_current_user
from app.enums import PermissionEntity as Entity
from app.enums import PermissionVerb as Verb
from app.exceptions import WasNotFoundException
from app.security import Permission, has_permission
from fastapi import APIRouter, Depends
from app.utils.filters import build_sort_instrument, build_where_instrument

logger = logging.getLogger()

instrument_router = APIRouter()

@instrument_router.post('/search', response_model=List[schemas.Instrument])
async def search_instruments(
    instrument_repo: repo.Instrument,
    filters: schemas.InstrumentFilters,
    _=Depends(has_permission([Permission(Verb.VIEW, Entity.INSTRUMENT)])),
) -> Optional[List[schemas.Instrument]]:
    """
    Get instruments based on a list of parameters

    Args:
        instrument_repo (repo.Company): dependency
            injection of the Instrument Repository

    Returns:
        schemas.Instrument: An Instrument object.
    """
    where = build_where_instrument(filters)
    order_list = build_sort_instrument(filters.sort)

    instruments = await instrument_repo.get_all(
        where_list=where or None,
        order_list=order_list or None,
        limit=filters.limit,
        offset=filters.offset,
    )
    return instruments


@instrument_router.get('/{instrument_id}', response_model=schemas.Instrument)
async def get_instrument(
    instrument_id: schemas.MonetaID,
    instrument_repo: repo.Instrument,
    _=Depends(has_permission([Permission(Verb.VIEW, Entity.INSTRUMENT)])),
) -> Optional[List[schemas.Instrument]]:
    """
    Get instrument by its id.

    Args:
        instrument_id (schemas.MonetaID) : uuid4
        instrument_repo (repo.Company): dependency
            injection of the Instrument Repository

    Returns:
        schemas.Instrument: An Instrument object.
    """
    instrument = await instrument_repo.get_by_id(instrument_id)
    if instrument:
        return instrument
    else:
        raise WasNotFoundException(
            detail=f'Instrument with ID {instrument_id} does not exist'
        )


# TODO: Make it a part of the workflow for
# creating on- and off-chaim representations.
# With this being the first step
@instrument_router.post('/', response_model=schemas.InstrumentCreate)
async def create_instrument(
    instrument_data: schemas.InstrumentCreate,
    instrument_repo: repo.Instrument,
    current_user=Depends(get_current_user),
    _=Depends(has_permission([Permission(Verb.CREATE, Entity.INSTRUMENT)])),
) -> schemas.Instrument:
    """
    Create a new instrument for off-chain

    Args:
        instrument_data: Company creation data
        instrument_repo: Company repository dependency
        current_user: Current User

    Returns:
        Instrument: The created instrument
    """
    internal_data = schemas.InstrumentCreateInternal(
        **instrument_data.dict(),
        issuer_id=current_user.company_id,
        created_by=current_user.id,
    )
    instrument = await instrument_repo.create(internal_data)
    return instrument
