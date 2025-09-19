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
from app.enums import InstrumentStatus
from app.exceptions import WasNotFoundException, InsufficientPermissionsException
from app.security import Permission, has_permission
from app.utils import validations
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

################################################################################
#                        Updating an instrument entity
################################################################################
@instrument_router.patch('/{instrument_id}', response_model=schemas.Instrument)
async def update_drafted_instrument(
    instrument_id: schemas.MonetaID,
    instrument_data: schemas.InstrumentDRAFTUpdate,
    instrument_repo: repo.Instrument,
    current_user=Depends(get_current_user),
    _=Depends(has_permission([Permission(Verb.UPDATE, Entity.INSTRUMENT)])),
) -> schemas.Instrument:
    """
    Allows updates to drafted instruments by all members of company.
    """

    # Check that the instrument exists
    instrument = await instrument_repo.get_by_id(instrument_id)
    if not instrument:
        raise WasNotFoundException(
            detail=f'Instrument with ID {instrument_id} does not exist'
        )

    # Check that the instrument has a status of DRAFT
    if instrument.instrument_status is not InstrumentStatus.DRAFT:
        raise InsufficientPermissionsException(
            detail=f'This instrument cannot be updated'
        )

    # Check that the user belongs to the same company 
    # as that which issues the DRAFT
    if instrument.issuer_id != current_user.company_id:
        raise InsufficientPermissionsException(
            detail=f'This instrument does not belong to you'
        )

    # Update entity checks
    # Check that the time is in the future
    if instrument_data.maturity_date:
        validations.ensure_future(instrument_data.maturity_date, 'maturity_date')
    # Check that the faceValue is more than 0
    if instrument_data.face_value:
        validations.ensure_positive(instrument_data.face_value, 'face_value')
    # Check that the maturityPayment is more than 0
    if instrument_data.maturity_payment:
        validations.ensure_positive(instrument_data.maturity_payment, 'maturity_payment')

    # Update the entity in the database
    updated = await instrument_repo.update_by_id(instrument_id, instrument_data)
    return updated


################################################################################
#                             Updating Instrument Status
################################################################################
# These actions relate to status of a note rather than to the
# maturity of the instrument.
# 
# 
# 1. DRAFT = User began creation of an instrument but not has finished.
#  At this stage they can make any corrections to the instrument as well delete
#  it altogether.
# 2. PENDING_APPROVAL = User submitted the instrument for approval.
#  No more changes can be made to the instrument. Before becomes publicly
#  availble for purchase ADMIN must approve this note
# 3. ACTIVE = instrument was approved and is currently being publicly
#  traded on-chain
# 4. MATURED = the date of the maturity of the instrument has passed
#  and it changed its status FROM ACTIVE.
# TODO: Add the following statuses:
# 5. REJECTED = For some reason an admin decided that an instrument
#  with status PENDING_APPROVAL cannot be publicly traded.

@instrument_router.post("/{instrument_id}/transition", response_model=schemas.Instrument)
async def update_status(
    instrument_id: schemas.MonetaID,
    body: schemas.InstrumentTransitionRequest,
    instrument_repo: repo.Instrument,
    current_user=Depends(get_current_user),
    _=Depends(has_permission([Permission(Verb.UPDATE, Entity.INSTRUMENT)])),
) -> schemas.Instrument:
    """
    A method that handles all logic for the instruments' statuses.
    """
    pass
