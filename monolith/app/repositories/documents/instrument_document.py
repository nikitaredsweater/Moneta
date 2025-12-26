"""
This module contains the functions to interact with the instrument_documents table.

All of the interaction with the instrument_documents table should be done through
this module.
"""

from typing import Annotated

from app import models, schemas
from app.repositories.base import BasePGRepository
from app.schemas.base import MonetaID
from app.utils.session import async_session
from fastapi import Depends


class InstrumentDocumentRepository(
    BasePGRepository[schemas.InstrumentDocument]
):
    class Meta:
        response_model = schemas.InstrumentDocument
        orm_model = models.InstrumentDocument
        exclusion_fields = None

    async def get_by_instrument_id(
        self, instrument_id: MonetaID
    ) -> list[schemas.InstrumentDocument]:
        """Get all document associations for an instrument."""
        return await self.get_all(
            [self.Meta.orm_model.instrument_id == instrument_id]
        )

    async def get_by_document_id(
        self, document_id: MonetaID
    ) -> list[schemas.InstrumentDocument]:
        """Get all instrument associations for a document."""
        return await self.get_all(
            [self.Meta.orm_model.document_id == document_id]
        )

    async def get_by_instrument_and_document(
        self, instrument_id: MonetaID, document_id: MonetaID
    ) -> schemas.InstrumentDocument | None:
        """Get a specific association by instrument and document IDs."""
        results = await self.get_all(
            [
                self.Meta.orm_model.instrument_id == instrument_id,
                self.Meta.orm_model.document_id == document_id,
            ]
        )
        return results[0] if results else None


InstrumentDocument = Annotated[
    InstrumentDocumentRepository,
    Depends(InstrumentDocumentRepository.make_fastapi_dep(async_session)),
]
