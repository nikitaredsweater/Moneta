"""
Instrument DTOs
"""

from datetime import date

from app.schemas.base import BaseDTO, CamelModel, MonetaID
from pydantic import Field
from app.enums import InstrumentStatus, MaturityStatus


class Instrument(BaseDTO):
    """
    Instrument Profile
    """
    name: str = Field(..., max_length=255)
    face_value: float
    currency: str = Field(..., min_length=3, max_length=3)
    maturity_date: date
    maturity_payment: float
    instrument_status: InstrumentStatus
    maturity_status: MaturityStatus
    issuer_id:MonetaID
    created_by:MonetaID

class InstrumentCreate(CamelModel):
    """
    Instrument Profile
    """
    name: str = Field(..., max_length=255)
    face_value: float
    currency: str = Field(..., min_length=3, max_length=3)
    maturity_date: date
    maturity_payment: float

class InstrumentCreateInternal(InstrumentCreate):
    """
    Instrument Profile
    """
    issuer_id:MonetaID
    created_by:MonetaID