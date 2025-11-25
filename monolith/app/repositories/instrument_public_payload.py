"""
This module contains the functions to interact with the entity for Public Instrument Representation.
All of the interaction with the user table should be done through this module.
"""

from typing import Annotated, Optional

from app import models, schemas
from app.repositories.base import BasePGRepository
from app.utils.session import async_session
from fastapi import Depends


class InstrumentPublicPayloadRepository(BasePGRepository[schemas.InstrumentPublicPayloadFull]):
    class Meta:
        response_model = schemas.InstrumentPublicPayloadFull  # This should be your schema
        orm_model = models.InstrumentPublicPayload  # This should be your ORM model
        exclusion_fields = None

    async def get_by_instrument_id_exact(
        self, instrument_id: schemas.MonetaID
    ) -> Optional[schemas.InstrumentPublicPayloadFull]:
        """
        Get a intrument public payload by instrument UUID
        Args:
            instrument_id: instrument UUID

        Returns:
            Instrument Public Payload if found, None otherwise
        """
        return await self.get_one([self.Meta.orm_model.instrument_id == instrument_id])


InstrumentPublicPayload = Annotated[
    InstrumentPublicPayloadRepository,
    Depends(InstrumentPublicPayloadRepository.make_fastapi_dep(async_session)),
]
