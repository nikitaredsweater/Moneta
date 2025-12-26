"""
InstrumentOwnership DTOs
Ownership history for instruments.
"""

from datetime import datetime
from typing import Optional

from app.enums import AcquisitionReason
from app.schemas.base import BaseDTO, CamelModel, MonetaID
from pydantic import ConfigDict, Field


class InstrumentOwnership(BaseDTO):
    """
    InstrumentOwnership DTO for responses.
    Represents a period of ownership for an instrument.
    """

    instrument_id: MonetaID
    owner_id: MonetaID
    acquired_at: datetime
    relinquished_at: Optional[datetime] = None
    acquisition_reason: AcquisitionReason

    model_config = ConfigDict(from_attributes=True)


class InstrumentOwnershipCreate(CamelModel):
    """
    Model for creating an instrument ownership record.
    Used when an instrument is first issued or ownership is transferred.
    """

    instrument_id: MonetaID
    owner_id: MonetaID
    acquired_at: datetime = Field(default_factory=datetime.now)
    acquisition_reason: AcquisitionReason = AcquisitionReason.ISSUANCE


class InstrumentOwnershipClose(CamelModel):
    """
    Model for closing an ownership record (setting relinquished_at).
    Records are never updated — only closed.
    """

    relinquished_at: datetime = Field(default_factory=datetime.now)
