"""
Instrument endpoints
"""

import logging
from typing import Dict, List, Optional

from app import repositories as repo
from app import schemas
from app.dependencies import get_current_user
from app.enums import InstrumentStatus, MaturityStatus
from app.enums import PermissionEntity as Entity
from app.enums import PermissionVerb as Verb
from app.enums import UserRole
from app.exceptions import (
    InsufficientPermissionsException,
    WasNotFoundException,
)
from app.security import Permission, has_permission
from app.utils import validations
from app.exceptions import FailedToCreateEntityException
from app.utils.filters.instrument_filters import build_sort_instrument, build_where_instrument
from fastapi import APIRouter, Depends

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
# creating on- and off-chain representations.
# With this being the first step
@instrument_router.post('/', response_model=schemas.Instrument)
async def create_instrument(
    instrument_data: schemas.InstrumentCreate,
    instrument_repo: repo.Instrument,
    public_payload_repo: repo.InstrumentPublicPayload,
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

    # TODO: Add verifications of the payload object

    internal_data = schemas.InstrumentCreateInternal(
        **instrument_data.model_dump(exclude={"public_payload"}),
        issuer_id=current_user.company_id,
        created_by=current_user.id,
    )

    instrument = await instrument_repo.create(internal_data)

    if instrument is None:
        raise FailedToCreateEntityException
    
    payload = {}
    if instrument_data.public_payload is not None:
        payload = instrument_data.public_payload

    public_payload = await public_payload_repo.create(
        schemas.InstrumentPublicPayloadFull(
            instrument_id=instrument.id,
            payload=payload,
        )
    )

    if public_payload is None:
        raise FailedToCreateEntityException

    instrument_with_payload = await instrument_repo.get_by_id(
        instrument.id
    )

    if instrument_with_payload is None:
        raise FailedToCreateEntityException # Should not be happenning

    return instrument_with_payload


################################################################################
#                        Updating  Instrument Entity
################################################################################
@instrument_router.patch('/{instrument_id}', response_model=schemas.Instrument)
async def update_drafted_instrument(
    instrument_id: schemas.MonetaID,
    instrument_data: schemas.InstrumentDRAFTUpdate,
    instrument_repo: repo.Instrument,
    public_payload_repo: repo.InstrumentPublicPayload,
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
        validations.ensure_future(
            instrument_data.maturity_date, 'maturity_date'
        )
    # Check that the faceValue is more than 0
    if instrument_data.face_value:
        validations.ensure_positive(instrument_data.face_value, 'face_value')
    # Check that the maturityPayment is more than 0
    if instrument_data.maturity_payment:
        validations.ensure_positive(
            instrument_data.maturity_payment, 'maturity_payment'
        )

    # Update the entity in the database
    instrument_data_trimmed = schemas.InstrumentDRAFTUpdate(
        **instrument_data.model_dump(exclude={"public_payload"}),
    )
    updated_instrument = await instrument_repo.update_by_id(instrument_id, instrument_data_trimmed)

    public_payload_id = None
    update_payload = instrument_data.public_payload
    if updated_instrument:
        if updated_instrument.public_payload:
            public_payload_id = updated_instrument.public_payload.id
    
    if public_payload_id is None:
        # Object is still not created. Create an object with passed payload
        await public_payload_repo.create(schemas.InstrumentPublicPayloadFull(
            instrument_id=instrument_id,
            payload=update_payload
        ))
    elif update_payload is not None:
        # Update the payload
        await public_payload_repo.update_by_id(public_payload_id, schemas.InstrumentPublicPayloadFull(
            payload=update_payload
        ))
    
    return await instrument_repo.get_by_id(instrument_id)


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
#
# 2. PENDING_APPROVAL = User submitted the instrument for approval.
#  No more changes can be made to the instrument. Before becomes publicly
#  availble for purchase ADMIN must approve this note
#
# 3. ACTIVE = instrument was approved and is currently being publicly
#  traded on-chain
#
# 4. MATURED = the date of the maturity of the instrument has passed
#  and it changed its status FROM ACTIVE.
#
# 5. REJECTED = For some reason an admin decided that an instrument
#  with status PENDING_APPROVAL cannot be publicly traded.

# Allowed graph: (status, user_type) -> next_status
TRANSITIONS: Dict[tuple[InstrumentStatus, UserRole], list[InstrumentStatus]] = {
    (InstrumentStatus.DRAFT, UserRole.ISSUER): [
        InstrumentStatus.PENDING_APPROVAL
    ],
    (InstrumentStatus.DRAFT, UserRole.ADMIN): [
        InstrumentStatus.PENDING_APPROVAL
    ],  # TODO: Remove after tests
    (InstrumentStatus.PENDING_APPROVAL, UserRole.ADMIN): [
        InstrumentStatus.REJECTED,
        InstrumentStatus.ACTIVE,
    ],
    # Transition from ACTIVE to MATURED should happen by a clock.
}


@instrument_router.post(
    "/{instrument_id}/transition", response_model=schemas.Instrument
)
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
    instrument = await instrument_repo.get_by_id(instrument_id)
    if not instrument:
        raise WasNotFoundException(
            detail=f'Instrument with ID {instrument_id} does not exist'
        )

    key = (instrument.instrument_status, current_user.role)
    allowed_next_statuses = TRANSITIONS.get(key, [])
    if body.new_status not in allowed_next_statuses:
        raise InsufficientPermissionsException(
            detail=f'You cannot perform this transition'
        )

    # FIXME: Doing to separate calls to DB is very not advised...
    updated = await instrument_repo.update_by_id(
        instrument_id,
        schemas.InstrumentStatusUpdate(instrument_status=body.new_status),
    )

    if updated:
        # Performing additional actions depending on the type of the new status
        # Received by the instrument
        if (
            body.new_status is InstrumentStatus.ACTIVE
            and updated.instrument_status is InstrumentStatus.ACTIVE
        ):
            # Double check in case the status did not change

            # Here we do actions that we need before the item goes public

            # Setting the maturity status to 'pending' - indicates that
            # the item is currently changing hands and the maturity settlement is
            # pending to happen.
            updated = await instrument_repo.update_by_id(
                instrument_id,
                schemas.InstrumentMaturityStatusUpdate(
                    maturity_status=MaturityStatus.DUE
                ),
            )

    return updated
