"""
Bid DTOs
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from app.enums import BidStatus
from app.schemas.base import BaseDTO, CamelModel, MonetaID
from pydantic import ConfigDict, Field

if TYPE_CHECKING:
    from app.schemas.listing import Listing


class Bid(BaseDTO):
    """
    Bid DTO for responses.
    """

    listing_id: MonetaID
    bidder_company_id: MonetaID
    bidder_user_id: MonetaID
    amount: float
    currency: str
    valid_until: Optional[datetime] = None
    status: BidStatus

    model_config = ConfigDict(from_attributes=True)


class BidWithListing(BaseDTO):
    """
    Bid DTO with nested Listing for includes.
    """

    listing_id: MonetaID
    bidder_company_id: MonetaID
    bidder_user_id: MonetaID
    amount: float
    currency: str
    valid_until: Optional[datetime] = None
    status: BidStatus
    listing: Optional['Listing'] = None

    model_config = ConfigDict(from_attributes=True)


class BidCreate(CamelModel):
    """
    Schema for creating a new bid.
    listing_id is required, bidder company and user are derived from context.
    """

    listing_id: MonetaID
    amount: float = Field(..., gt=0, description="Bid amount must be positive")
    currency: str = Field(
        ..., min_length=3, max_length=3, description="ISO 4217 currency code"
    )
    valid_until: Optional[datetime] = None


class BidCreateInternal(CamelModel):
    """
    Internal schema for creating a bid with all fields.
    """

    listing_id: MonetaID
    bidder_company_id: MonetaID
    bidder_user_id: MonetaID
    amount: float
    currency: str
    valid_until: Optional[datetime] = None
    status: BidStatus = BidStatus.PENDING


class BidStatusUpdate(CamelModel):
    """
    Schema for updating the bid status.
    """

    status: BidStatus


class BidFilters(CamelModel):
    """
    Schema for bid search parameters.
    """

    listing_id: Optional[List[MonetaID]] = None
    bidder_company_id: Optional[List[MonetaID]] = None
    bidder_user_id: Optional[List[MonetaID]] = None
    status: Optional[BidStatus] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    currency: Optional[str] = None

    sort: Optional[str] = '-created_at'
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


# Import here to avoid circular import
from app.schemas.listing import Listing  # noqa: E402

BidWithListing.model_rebuild()
