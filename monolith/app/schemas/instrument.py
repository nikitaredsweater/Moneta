"""
Instrument DTOs
"""

from datetime import date
from typing import List, Optional, Dict, Any

from app.enums import InstrumentStatus, MaturityStatus, TradingStatus
from app.exceptions import EmptyEntityException
from app.schemas.base import BaseDTO, CamelModel, MonetaID
from app.schemas.instrument_public_payload import InstrumentPublicPayloadFull, InstrumentPublicPayloadCreate
from pydantic import Field, root_validator, ConfigDict


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
    trading_status: TradingStatus
    issuer_id: MonetaID
    created_by: MonetaID

    public_payload: Optional[InstrumentPublicPayloadFull] = None

    model_config = ConfigDict(from_attributes=True)


class InstrumentFilters(CamelModel):
    """
    Schema to set the search parameters for instruments
    """

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
    trading_status: Optional[TradingStatus] = None

    # Now arrays:
    issuer_id: Optional[List[MonetaID]] = None
    created_by: Optional[List[MonetaID]] = None

    sort: Optional[str] = '-created_at'
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
    public_payload: Optional[Dict[str, Any]] = None

class InstrumentDRAFTUpdate(CamelModel):
    """
    For DRAFT Updates
    """

    name: Optional[str] = Field(None, max_length=255)
    face_value: Optional[float] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    maturity_date: Optional[date] = None
    maturity_payment: Optional[float] = None
    public_payload: Optional[Dict[str, Any]] = None

    @root_validator(pre=True)
    def at_least_one_field(cls, values):
        if not any(
            v is not None
            for k, v in values.items()
            if k
            in {
                'name',
                'face_value',
                'currency',
                'maturity_date',
                'maturity_payment',
                'public_payload'
            }
        ):
            raise EmptyEntityException
        # optional: normalize currency to upper
        cur = values.get('currency')
        if isinstance(cur, str):
            values['currency'] = cur.upper()
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


class InstrumentMaturityStatusUpdate(CamelModel):
    """
    to update the maturity status
    """

    maturity_status: MaturityStatus


class InstrumentCreateInternal(CamelModel):
    """
    Internal instrument profile
    """

    issuer_id: MonetaID
    created_by: MonetaID

    name: str = Field(..., max_length=255)
    face_value: float
    currency: str = Field(..., min_length=3, max_length=3)
    maturity_date: date
    maturity_payment: float

    instrument_status: InstrumentStatus = InstrumentStatus.DRAFT
    maturity_status: MaturityStatus = MaturityStatus.NOT_DUE
    trading_status: TradingStatus = TradingStatus.DRAFT

    # public_payload: Optional[InstrumentPublicPayloadFull] = None