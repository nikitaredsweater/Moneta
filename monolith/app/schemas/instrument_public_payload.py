"""
DTO for an object that shows un-structured data of an instrument
public representation. Used for NFT-related activities.
"""

from typing import Dict, Any
from app.schemas.base import BaseDTO, MonetaID

from pydantic import ConfigDict

class InstrumentPublicPayloadFull(BaseDTO):
    """
    Base model for InstrumentPublicPayload. Contains all fields of the entity.
    """
    instrument_id: MonetaID
    payload: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)
