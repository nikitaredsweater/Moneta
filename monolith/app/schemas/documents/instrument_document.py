"""
InstrumentDocument DTOs
Association between instruments and documents.
"""

from datetime import datetime

from app.schemas.base import BaseDTO, CamelModel, MonetaID
from pydantic import Field


class InstrumentDocument(BaseDTO):
    """
    InstrumentDocument DTO for responses.
    """

    instrument_id: MonetaID
    document_id: MonetaID


class InstrumentDocumentCreate(CamelModel):
    """
    Model for creating an instrument-document association.
    """

    instrument_id: MonetaID
    document_id: MonetaID
    created_at: datetime = Field(default_factory=datetime.now)
