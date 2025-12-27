"""
Ask DTOs
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from app.enums import AskStatus, ExecutionMode
from app.schemas.base import BaseDTO, CamelModel, MonetaID
from pydantic import ConfigDict, Field

if TYPE_CHECKING:
    from app.schemas.listing import Listing


class Ask(BaseDTO):
    """
    Ask DTO for responses.
    """

    listing_id: MonetaID
    asker_company_id: MonetaID
    asker_user_id: MonetaID
    amount: float
    currency: str
    valid_until: Optional[datetime] = None
    execution_mode: ExecutionMode
    binding: bool
    status: AskStatus

    model_config = ConfigDict(from_attributes=True)


class AskWithListing(BaseDTO):
    """
    Ask DTO with nested Listing for includes.
    """

    listing_id: MonetaID
    asker_company_id: MonetaID
    asker_user_id: MonetaID
    amount: float
    currency: str
    valid_until: Optional[datetime] = None
    execution_mode: ExecutionMode
    binding: bool
    status: AskStatus
    listing: Optional['Listing'] = None

    model_config = ConfigDict(from_attributes=True)


class AskCreate(CamelModel):
    """
    Schema for creating a new ask.
    listing_id is required, asker company and user are derived from context.
    """

    listing_id: MonetaID
    amount: float = Field(..., gt=0, description="Ask amount must be positive")
    currency: str = Field(
        ..., min_length=3, max_length=3, description="ISO 4217 currency code"
    )
    valid_until: Optional[datetime] = None
    execution_mode: ExecutionMode = ExecutionMode.MANUAL
    binding: bool = False


class AskCreateInternal(CamelModel):
    """
    Internal schema for creating an ask with all fields.
    """

    listing_id: MonetaID
    asker_company_id: MonetaID
    asker_user_id: MonetaID
    amount: float
    currency: str
    valid_until: Optional[datetime] = None
    execution_mode: ExecutionMode = ExecutionMode.MANUAL
    binding: bool = False
    status: AskStatus = AskStatus.ACTIVE


class AskStatusUpdate(CamelModel):
    """
    Schema for updating the ask status.
    """

    status: AskStatus


class AskUpdate(CamelModel):
    """
    Schema for updating ask price or validity.
    Only amount, currency, and valid_until can be updated.
    """

    amount: Optional[float] = Field(
        None, gt=0, description="Ask amount must be positive"
    )
    currency: Optional[str] = Field(
        None, min_length=3, max_length=3, description="ISO 4217 currency code"
    )
    valid_until: Optional[datetime] = None


class AskFilters(CamelModel):
    """
    Schema for ask search parameters.
    """

    listing_id: Optional[List[MonetaID]] = None
    asker_company_id: Optional[List[MonetaID]] = None
    asker_user_id: Optional[List[MonetaID]] = None
    status: Optional[AskStatus] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    currency: Optional[str] = None
    execution_mode: Optional[ExecutionMode] = None
    binding: Optional[bool] = None

    sort: Optional[str] = '-created_at'
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


# Import here to avoid circular import
from app.schemas.listing import Listing  # noqa: E402

AskWithListing.model_rebuild()
