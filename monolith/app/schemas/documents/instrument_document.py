"""
InstrumentDocument DTOs
Association between instruments and documents.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from app.schemas.base import BaseDTO, CamelModel, MonetaID
from pydantic import ConfigDict, Field

if TYPE_CHECKING:
    from app.schemas.documents.document import Document


class InstrumentDocument(BaseDTO):
    """
    InstrumentDocument DTO for responses.
    """

    instrument_id: MonetaID
    document_id: MonetaID


class InstrumentDocumentWithDocument(BaseDTO):
    """
    InstrumentDocument DTO with nested Document for includes.
    """

    instrument_id: MonetaID
    document_id: MonetaID
    document: Optional['Document'] = None

    model_config = ConfigDict(from_attributes=True)


class InstrumentDocumentCreate(CamelModel):
    """
    Model for creating an instrument-document association.
    """

    instrument_id: MonetaID
    document_id: MonetaID
    created_at: datetime = Field(default_factory=datetime.now)


# Import here to avoid circular import
from app.schemas.documents.document import Document  # noqa: E402

InstrumentDocumentWithDocument.model_rebuild()
