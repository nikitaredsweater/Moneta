"""
This module contains the functions to interact with the instrument_ownerships table.

All of the interaction with the instrument_ownerships table should be done through
this module.
"""

from typing import Annotated

from app import models, schemas
from app.repositories.base import BasePGRepository
from app.schemas.base import MonetaID
from app.utils.session import async_session
from fastapi import Depends


class InstrumentOwnershipRepository(
    BasePGRepository[schemas.InstrumentOwnership]
):
    class Meta:
        response_model = schemas.InstrumentOwnership
        orm_model = models.InstrumentOwnership
        exclusion_fields = None

    async def get_by_instrument_id(
        self, instrument_id: MonetaID
    ) -> list[schemas.InstrumentOwnership]:
        """Get all ownership records for an instrument."""
        return await self.get_all(
            [self.Meta.orm_model.instrument_id == instrument_id]
        )

    async def get_by_owner_id(
        self, owner_id: MonetaID
    ) -> list[schemas.InstrumentOwnership]:
        """Get all ownership records for an owner (company)."""
        return await self.get_all(
            [self.Meta.orm_model.owner_id == owner_id]
        )

    async def get_active_by_instrument_id(
        self, instrument_id: MonetaID
    ) -> list[schemas.InstrumentOwnership]:
        """Get all active (non-relinquished) ownership records for an instrument."""
        return await self.get_all(
            [
                self.Meta.orm_model.instrument_id == instrument_id,
                self.Meta.orm_model.relinquished_at.is_(None),
            ]
        )

    async def get_active_by_owner_id(
        self, owner_id: MonetaID
    ) -> list[schemas.InstrumentOwnership]:
        """Get all active (non-relinquished) ownership records for an owner."""
        return await self.get_all(
            [
                self.Meta.orm_model.owner_id == owner_id,
                self.Meta.orm_model.relinquished_at.is_(None),
            ]
        )

    async def get_active_by_instrument_and_owner(
        self, instrument_id: MonetaID, owner_id: MonetaID
    ) -> schemas.InstrumentOwnership | None:
        """
        Get active ownership record for a specific instrument and owner.
        Returns None if no active ownership exists.
        """
        results = await self.get_all(
            [
                self.Meta.orm_model.instrument_id == instrument_id,
                self.Meta.orm_model.owner_id == owner_id,
                self.Meta.orm_model.relinquished_at.is_(None),
            ]
        )
        return results[0] if results else None

    async def get_current_owner(
        self, instrument_id: MonetaID
    ) -> schemas.InstrumentOwnership | None:
        """
        Get the current (active) owner of an instrument.
        Returns None if no active ownership exists.
        """
        results = await self.get_active_by_instrument_id(instrument_id)
        # There should be at most one active owner per instrument
        return results[0] if results else None


InstrumentOwnership = Annotated[
    InstrumentOwnershipRepository,
    Depends(InstrumentOwnershipRepository.make_fastapi_dep(async_session)),
]
