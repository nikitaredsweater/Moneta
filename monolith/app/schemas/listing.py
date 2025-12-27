"""
Listing DTOs
"""

from typing import TYPE_CHECKING, List, Optional

from app.enums import ListingStatus
from app.schemas.base import BaseDTO, CamelModel, MonetaID
from pydantic import ConfigDict, Field

if TYPE_CHECKING:
    from app.schemas.instrument import Instrument


class Listing(BaseDTO):
    """
    Listing DTO for responses.
    """

    instrument_id: MonetaID
    seller_company_id: MonetaID
    listing_creator_user_id: MonetaID
    status: ListingStatus

    model_config = ConfigDict(from_attributes=True)


class ListingWithInstrument(BaseDTO):
    """
    Listing DTO with nested Instrument for includes.
    """

    instrument_id: MonetaID
    seller_company_id: MonetaID
    listing_creator_user_id: MonetaID
    status: ListingStatus
    instrument: Optional['Instrument'] = None

    model_config = ConfigDict(from_attributes=True)


class ListingCreate(CamelModel):
    """
    Schema for creating a new listing.
    Only instrument_id is required - seller and creator are derived from context.
    """

    instrument_id: MonetaID


class ListingCreateInternal(CamelModel):
    """
    Internal schema for creating a listing with all fields.
    """

    instrument_id: MonetaID
    seller_company_id: MonetaID
    listing_creator_user_id: MonetaID
    status: ListingStatus = ListingStatus.OPEN


class ListingStatusUpdate(CamelModel):
    """
    Schema for updating the listing status.
    """

    status: ListingStatus


class ListingFilters(CamelModel):
    """
    Schema for listing search parameters.
    """

    instrument_id: Optional[List[MonetaID]] = None
    seller_company_id: Optional[List[MonetaID]] = None
    listing_creator_user_id: Optional[List[MonetaID]] = None
    status: Optional[ListingStatus] = None

    sort: Optional[str] = '-created_at'
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


# Import here to avoid circular import
from app.schemas.instrument import Instrument  # noqa: E402

ListingWithInstrument.model_rebuild()
