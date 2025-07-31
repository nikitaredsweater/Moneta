"""
Instrument DTOs
"""

from datetime import date

from app.schemas.base import BaseDTO, CamelModel
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

class InstrumentCreate(CamelModel):
    """
    Instrument Profile
    """
    name: str = Field(..., max_length=255)
    face_value: float
    currency: str = Field(..., min_length=3, max_length=3)
    maturity_date: date
    maturity_payment: float