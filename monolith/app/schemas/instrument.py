"""
Instrument DTOs
"""

from datetime import date

from typing import Optional, List
from app.schemas.base import BaseDTO, CamelModel, MonetaID
from pydantic import Field, root_validator
from app.enums import InstrumentStatus, MaturityStatus
from app.exceptions import EmptyEntityException


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

class InstrumentFilters(CamelModel):
    """schema to set the search parameters for instruments."""
    min_face_value: Optional[float] = None
    max_face_value: Optional[float] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)

    maturity_date_after: Optional[date] = None
    maturity_date_before: Optional[date] = None

    created_at_after: Optional[date] = None
    created_at_before: Optional[date] = None

    min_maturity_payment: Optional[float] = None
    max_maturity_payment: Optional[float] = None

    instrument_status: Optional[InstrumentStatus] = None
    maturity_status: Optional[MaturityStatus] = None

    # Now arrays:
    issuer_id: Optional[List[MonetaID]] = None
    created_by: Optional[List[MonetaID]] = None

    sort: Optional[str] = "-created_at"
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)  # optional but useful for pagination


class InstrumentCreate(CamelModel):
    """
    Instrument Profile
    """
    name: str = Field(..., max_length=255)
    face_value: float
    currency: str = Field(..., min_length=3, max_length=3)
    maturity_date: date
    maturity_payment: float

class InstrumentDRAFTUpdate(CamelModel):
    """
    For DRAFT Updates
    """
    name: Optional[str] = Field(None, max_length=255)
    face_value: Optional[float] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    maturity_date: Optional[date] = None
    maturity_payment: Optional[float] = None

    @root_validator(pre=True)
    def at_least_one_field(cls, values):
        if not any(v is not None for k, v in values.items() if k in {
            "name", "face_value", "currency", "maturity_date", "maturity_payment"
        }):
            raise EmptyEntityException
        # optional: normalize currency to upper
        cur = values.get("currency")
        if isinstance(cur, str):
            values["currency"] = cur.upper()
        return values
    
class InstrumentTransitionRequest(CamelModel):
    """
    schema used for when user wants to update the status of an instrument.
    """
    new_status: InstrumentStatus

class InstrumentStatusUpdate(CamelModel):
    """
    to update the status
    """
    instrument_status: InstrumentStatus


class InstrumentCreateInternal(InstrumentCreate):
    """
    Instrument Profile
    """
    issuer_id:MonetaID
    created_by:MonetaID