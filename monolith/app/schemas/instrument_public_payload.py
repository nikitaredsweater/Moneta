"""
DTO for an object that shows un-structured data of an instrument
public representation. Used for NFT-related activities.
"""

from typing import Dict, Any
from app.schemas.base import BaseDTO, MonetaID, CamelModel

from pydantic import ConfigDict

class InstrumentPublicPayloadFull(BaseDTO):
    """
    Base model for InstrumentPublicPayload. Contains all fields of the entity.
    """
    instrument_id: MonetaID
    payload: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)

class InstrumentPublicPayloadCreate(CamelModel):
    """
    Model to pass as a body when creating a new instrument
    """
    payload: Dict[str, Any]
