"""
Instrument Ownership Service.

This module contains service functions for managing instrument ownership.
Ownership records track the history of who owns an instrument and when.

Key rules:
    - Records are never updated — only closed (relinquished_at set) and new ones inserted
    - At most one active row per (instrument, owner) combination
    - Active ownership has relinquished_at = NULL

Responsibilities:
    - Recording initial ownership when instrument is issued/approved
    - Transferring ownership between companies
    - Querying current and historical ownership
"""

import logging
from datetime import datetime

from app import schemas
from app.enums import AcquisitionReason
from app.exceptions import EntityAlreadyExistsException, WasNotFoundException
from app.repositories import InstrumentOwnershipRepository
from app.schemas.base import MonetaID

logger = logging.getLogger(__name__)


async def record_issuance(
    repo: InstrumentOwnershipRepository,
    instrument_id: MonetaID,
    owner_id: MonetaID,
) -> schemas.InstrumentOwnership:
    """
    Record initial ownership when an instrument is issued/approved.

    This should be called when an instrument transitions to ACTIVE status.
    The issuer company becomes the initial owner.

    Args:
        repo: The InstrumentOwnership repository instance.
        instrument_id: The ID of the instrument being issued.
        owner_id: The ID of the company that will own the instrument (issuer).

    Returns:
        InstrumentOwnership: The created ownership record.

    Raises:
        EntityAlreadyExistsException: If active ownership already exists.
    """
    logger.debug(
        '[BUSINESS] Recording instrument issuance | instrument_id=%s | owner_id=%s',
        instrument_id,
        owner_id,
    )

    # Check if there's already an active ownership for this instrument
    existing = await repo.get_current_owner(instrument_id)
    if existing:
        logger.warning(
            '[BUSINESS] Instrument already has active ownership | '
            'instrument_id=%s | existing_owner_id=%s',
            instrument_id,
            existing.owner_id,
        )
        raise EntityAlreadyExistsException(
            detail='This instrument already has an active owner'
        )

    ownership = await repo.create(
        schemas.InstrumentOwnershipCreate(
            instrument_id=instrument_id,
            owner_id=owner_id,
            acquired_at=datetime.now(),
            acquisition_reason=AcquisitionReason.ISSUANCE,
        )
    )

    logger.info(
        '[BUSINESS] Instrument issuance recorded | ownership_id=%s | '
        'instrument_id=%s | owner_id=%s',
        ownership.id,
        instrument_id,
        owner_id,
    )
    return ownership


async def transfer_ownership(
    repo: InstrumentOwnershipRepository,
    instrument_id: MonetaID,
    from_owner_id: MonetaID,
    to_owner_id: MonetaID,
    reason: AcquisitionReason = AcquisitionReason.TRADE,
) -> schemas.InstrumentOwnership:
    """
    Transfer ownership of an instrument from one company to another.

    This closes the current ownership record and creates a new one.
    Both operations happen atomically within the repository's session.

    Args:
        repo: The InstrumentOwnership repository instance.
        instrument_id: The ID of the instrument being transferred.
        from_owner_id: The ID of the current owner company.
        to_owner_id: The ID of the new owner company.
        reason: The reason for transfer (TRADE or ASSIGNMENT).

    Returns:
        InstrumentOwnership: The new ownership record for the new owner.

    Raises:
        WasNotFoundException: If no active ownership exists for from_owner_id.
        EntityAlreadyExistsException: If to_owner_id already has active ownership.
    """
    logger.debug(
        '[BUSINESS] Transferring instrument ownership | instrument_id=%s | '
        'from_owner=%s | to_owner=%s | reason=%s',
        instrument_id,
        from_owner_id,
        to_owner_id,
        reason.value,
    )

    # Validate the current ownership
    current_ownership = await repo.get_active_by_instrument_and_owner(
        instrument_id, from_owner_id
    )
    if not current_ownership:
        logger.warning(
            '[BUSINESS] No active ownership found for transfer | '
            'instrument_id=%s | from_owner=%s',
            instrument_id,
            from_owner_id,
        )
        raise WasNotFoundException(
            detail=f'No active ownership found for owner {from_owner_id}'
        )

    # Check that the new owner doesn't already have active ownership
    existing_new_owner = await repo.get_active_by_instrument_and_owner(
        instrument_id, to_owner_id
    )
    if existing_new_owner:
        logger.warning(
            '[BUSINESS] New owner already has active ownership | '
            'instrument_id=%s | to_owner=%s',
            instrument_id,
            to_owner_id,
        )
        raise EntityAlreadyExistsException(
            detail=f'Owner {to_owner_id} already has active ownership of this instrument'
        )

    transfer_time = datetime.now()

    # Close the current ownership record
    await repo.update_by_id(
        current_ownership.id,
        schemas.InstrumentOwnershipClose(relinquished_at=transfer_time),
    )

    logger.debug(
        '[BUSINESS] Closed previous ownership | ownership_id=%s | '
        'relinquished_at=%s',
        current_ownership.id,
        transfer_time,
    )

    # Create new ownership record
    new_ownership = await repo.create(
        schemas.InstrumentOwnershipCreate(
            instrument_id=instrument_id,
            owner_id=to_owner_id,
            acquired_at=transfer_time,
            acquisition_reason=reason,
        )
    )

    logger.info(
        '[BUSINESS] Ownership transferred | instrument_id=%s | '
        'from_owner=%s | to_owner=%s | new_ownership_id=%s | reason=%s',
        instrument_id,
        from_owner_id,
        to_owner_id,
        new_ownership.id,
        reason.value,
    )
    return new_ownership


async def get_current_owner(
    repo: InstrumentOwnershipRepository,
    instrument_id: MonetaID,
) -> schemas.InstrumentOwnership | None:
    """
    Get the current owner of an instrument.

    Args:
        repo: The InstrumentOwnership repository instance.
        instrument_id: The ID of the instrument.

    Returns:
        InstrumentOwnership | None: The active ownership record, or None if none exists.
    """
    return await repo.get_current_owner(instrument_id)


async def get_ownership_history(
    repo: InstrumentOwnershipRepository,
    instrument_id: MonetaID,
) -> list[schemas.InstrumentOwnership]:
    """
    Get the complete ownership history of an instrument.

    Args:
        repo: The InstrumentOwnership repository instance.
        instrument_id: The ID of the instrument.

    Returns:
        List of all ownership records (active and closed) for the instrument.
    """
    return await repo.get_by_instrument_id(instrument_id)
