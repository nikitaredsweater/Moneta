"""
Instrument endpoints
"""

import logging
from typing import Dict, List, Optional, Set

from app import repositories as repo
from app import schemas
from app.dependencies import get_current_user, parse_instrument_includes
from app.enums import InstrumentInclude, InstrumentStatus, MaturityStatus
from app.enums import PermissionEntity as Entity
from app.enums import PermissionVerb as Verb
from app.enums import UserRole
from app.exceptions import (
    EntityAlreadyExistsException,
    FailedToCreateEntityException,
    InsufficientPermissionsException,
    WasNotFoundException,
)
from app.security import Permission, has_permission
from app.utils import validations
from app.utils.filters.instrument_filters import build_sort_instrument, build_where_instrument
from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)
instrument_router = APIRouter()


def map_instrument_includes_to_rel_names(includes: Set[InstrumentInclude]) -> List[str]:
    """
    Map include enums to actual relationship attribute names on models.Instrument.
    """
    rel_map = {
        InstrumentInclude.DOCUMENTS: 'instrument_documents',
    }
    return [rel_map[i] for i in includes if i in rel_map]


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
    logger.debug(
        '[BUSINESS] Searching instruments | limit=%d | offset=%d',
        filters.limit,
        filters.offset,
    )
    where = build_where_instrument(filters)
    order_list = build_sort_instrument(filters.sort)

    instruments = await instrument_repo.get_all(
        where_list=where or None,
        order_list=order_list or None,
        limit=filters.limit,
        offset=filters.offset,
    )
    logger.info('[BUSINESS] Instrument search completed | results=%d', len(instruments))
    return instruments


@instrument_router.get('/{instrument_id}', response_model=schemas.InstrumentIncludes)
async def get_instrument(
    instrument_id: schemas.MonetaID,
    instrument_repo: repo.Instrument,
    includes: Set[InstrumentInclude] = Depends(parse_instrument_includes),
    _=Depends(has_permission([Permission(Verb.VIEW, Entity.INSTRUMENT)])),
) -> schemas.InstrumentIncludes:
    """
    Get instrument by its id.

    Args:
        instrument_id (schemas.MonetaID) : uuid4
        instrument_repo (repo.Instrument): dependency
            injection of the Instrument Repository
        includes: Optional comma-separated list of related entities to include.
            Allowed: documents

    Returns:
        schemas.InstrumentIncludes: An Instrument object with optional includes.
    """
    logger.debug(
        '[BUSINESS] Fetching instrument | instrument_id=%s | includes=%s',
        instrument_id,
        list(includes) if includes else [],
    )
    rel_names = map_instrument_includes_to_rel_names(includes)

    if rel_names:
        # We want relations → eager-load & deserialize into extended DTO
        instrument = await instrument_repo.get_by_id(
            pk=instrument_id,
            includes=rel_names,
            custom_model=schemas.InstrumentIncludes,
        )
        if not instrument:
            logger.warning(
                '[BUSINESS] Instrument not found | instrument_id=%s', instrument_id
            )
            raise WasNotFoundException(
                detail=f'Instrument with ID {instrument_id} does not exist'
            )

        logger.info(
            '[BUSINESS] Instrument retrieved with includes | instrument_id=%s | '
            'includes=%s',
            instrument_id,
            rel_names,
        )
        return instrument

    # No includes → use base DTO (no relationships touched)
    base = await instrument_repo.get_by_id(pk=instrument_id)
    if not base:
        logger.warning(
            '[BUSINESS] Instrument not found | instrument_id=%s', instrument_id
        )
        raise WasNotFoundException(
            detail=f'Instrument with ID {instrument_id} does not exist'
        )

    logger.info('[BUSINESS] Instrument retrieved | instrument_id=%s', instrument_id)
    # Convert base → extended shape, relations stay None
    return schemas.InstrumentIncludes(**base.model_dump())


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

    logger.debug(
        '[BUSINESS] Creating instrument | name=%s | issuer_id=%s | created_by=%s',
        instrument_data.name,
        current_user.company_id,
        current_user.id,
    )
    internal_data = schemas.InstrumentCreateInternal(
        **instrument_data.model_dump(exclude={"public_payload"}),
        issuer_id=current_user.company_id,
        created_by=current_user.id,
    )

    instrument = await instrument_repo.create(internal_data)
    logger.info(
        '[BUSINESS] Instrument created | instrument_id=%s | name=%s | issuer_id=%s',
        instrument.id,
        instrument.name,
        instrument.issuer_id,
    )

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
    logger.debug(
        '[BUSINESS] Updating draft instrument | instrument_id=%s | requested_by=%s',
        instrument_id,
        current_user.id,
    )

    # Check that the instrument exists
    instrument = await instrument_repo.get_by_id(instrument_id)
    if not instrument:
        logger.warning(
            '[BUSINESS] Instrument not found for update | instrument_id=%s',
            instrument_id,
        )
        raise WasNotFoundException(
            detail=f'Instrument with ID {instrument_id} does not exist'
        )

    # Check that the instrument has a status of DRAFT
    if instrument.instrument_status is not InstrumentStatus.DRAFT:
        logger.warning(
            '[BUSINESS] Cannot update non-draft instrument | instrument_id=%s | '
            'status=%s',
            instrument_id,
            instrument.instrument_status,
        )
        raise InsufficientPermissionsException(
            detail='This instrument cannot be updated'
        )

    # Check that the user belongs to the same company
    # as that which issues the DRAFT
    if instrument.issuer_id != current_user.company_id:
        logger.warning(
            '[BUSINESS] Forbidden instrument update | instrument_id=%s | '
            'issuer_id=%s | requester_company=%s',
            instrument_id,
            instrument.issuer_id,
            current_user.company_id,
        )
        raise InsufficientPermissionsException(
            detail='This instrument does not belong to you'
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

    # Update the entity in the database (only if there are non-payload fields to update)
    instrument_fields = instrument_data.model_dump(exclude={"public_payload"}, exclude_none=True)
    if instrument_fields:
        updated_instrument = await instrument_repo.update_by_id(
            instrument_id,
            schemas.InstrumentDRAFTUpdate(**instrument_fields),
        )
    else:
        updated_instrument = instrument

    public_payload_id = None
    update_payload = instrument_data.public_payload
    if updated_instrument.public_payload:
        public_payload_id = updated_instrument.public_payload.id

    if update_payload is not None:
        if public_payload_id is None:
            # Object is still not created. Create an object with passed payload
            await public_payload_repo.create(schemas.InstrumentPublicPayloadFull(
                instrument_id=instrument_id,
                payload=update_payload
            ))
        else:
            # Update the payload
            await public_payload_repo.update_by_id(public_payload_id, schemas.InstrumentPublicPayloadFull(
                payload=update_payload
            ))

    logger.info(
        '[BUSINESS] Draft instrument updated | instrument_id=%s | updated_by=%s',
        instrument_id,
        current_user.id,
    )
    
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
    logger.debug(
        '[BUSINESS] Instrument status transition | instrument_id=%s | '
        'new_status=%s | requested_by=%s | role=%s',
        instrument_id,
        body.new_status,
        current_user.id,
        current_user.role,
    )
    instrument = await instrument_repo.get_by_id(instrument_id)
    if not instrument:
        logger.warning(
            '[BUSINESS] Instrument not found for transition | instrument_id=%s',
            instrument_id,
        )
        raise WasNotFoundException(
            detail=f'Instrument with ID {instrument_id} does not exist'
        )

    key = (instrument.instrument_status, current_user.role)
    allowed_next_statuses = TRANSITIONS.get(key, [])
    if body.new_status not in allowed_next_statuses:
        logger.warning(
            '[BUSINESS] Invalid status transition | instrument_id=%s | '
            'current_status=%s | requested_status=%s | role=%s',
            instrument_id,
            instrument.instrument_status,
            body.new_status,
            current_user.role,
        )
        raise InsufficientPermissionsException(
            detail='You cannot perform this transition'
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
            logger.info(
                '[BUSINESS] Instrument activated | instrument_id=%s | '
                'maturity_status=%s',
                instrument_id,
                MaturityStatus.DUE,
            )

    logger.info(
        '[BUSINESS] Instrument status transitioned | instrument_id=%s | '
        'old_status=%s | new_status=%s | transitioned_by=%s',
        instrument_id,
        instrument.instrument_status,
        body.new_status,
        current_user.id,
    )
    return updated


################################################################################
#                        Instrument Document Association
################################################################################
@instrument_router.post(
    "/{instrument_id}/documents/{document_id}",
    response_model=schemas.InstrumentDocument,
)
async def associate_document_with_instrument(
    instrument_id: schemas.MonetaID,
    document_id: schemas.MonetaID,
    instrument_repo: repo.Instrument,
    document_repo: repo.Document,
    instrument_document_repo: repo.InstrumentDocument,
    _=Depends(has_permission([Permission(Verb.UPDATE, Entity.INSTRUMENT)])),
) -> schemas.InstrumentDocument:
    """
    Associate a document with an instrument.

    Args:
        instrument_id: The ID of the instrument.
        document_id: The ID of the document to associate.
        instrument_repo: Instrument repository dependency.
        document_repo: Document repository dependency.
        instrument_document_repo: InstrumentDocument repository dependency.

    Returns:
        InstrumentDocument: The created association.

    Raises:
        WasNotFoundException: If instrument or document does not exist.
        EntityAlreadyExistsException: If association already exists.
        FailedToCreateEntityException: If association creation fails.
    """
    logger.debug(
        '[BUSINESS] Associating document with instrument | '
        'instrument_id=%s | document_id=%s',
        instrument_id,
        document_id,
    )

    # Check that the instrument exists
    instrument = await instrument_repo.get_by_id(instrument_id)
    if not instrument:
        logger.warning(
            '[BUSINESS] Instrument not found for document association | '
            'instrument_id=%s',
            instrument_id,
        )
        raise WasNotFoundException(
            detail=f'Instrument with ID {instrument_id} does not exist'
        )

    # Check that the document exists
    document = await document_repo.get_by_id(document_id)
    if not document:
        logger.warning(
            '[BUSINESS] Document not found for instrument association | '
            'document_id=%s',
            document_id,
        )
        raise WasNotFoundException(
            detail=f'Document with ID {document_id} does not exist'
        )

    # Check that the association does not already exist
    existing = await instrument_document_repo.get_by_instrument_and_document(
        instrument_id, document_id
    )
    if existing:
        logger.warning(
            '[BUSINESS] Document already associated with instrument | '
            'instrument_id=%s | document_id=%s',
            instrument_id,
            document_id,
        )
        raise EntityAlreadyExistsException(
            detail='This document is already associated with this instrument'
        )

    # Create the association
    association = await instrument_document_repo.create(
        schemas.InstrumentDocumentCreate(
            instrument_id=instrument_id,
            document_id=document_id,
        )
    )

    if not association:
        logger.error(
            '[BUSINESS] Failed to create document association | '
            'instrument_id=%s | document_id=%s',
            instrument_id,
            document_id,
        )
        raise FailedToCreateEntityException(
            detail='Failed to associate document with instrument'
        )

    logger.info(
        '[BUSINESS] Document associated with instrument | '
        'instrument_id=%s | document_id=%s | association_id=%s',
        instrument_id,
        document_id,
        association.id,
    )
    return association
