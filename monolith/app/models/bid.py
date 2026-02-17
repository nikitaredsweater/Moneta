"""
Bid ORM model
Represents a bid placed on a listing by a company.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from app.enums import BidStatus
from app.models.base import Base, BaseEntity
from sqlalchemy import DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.listing import Listing
    from app.models.user import User


class Bid(Base, BaseEntity):
    """
    Bid on a listing.

    Represents an offer made by a company to purchase the instrument
    listed in a listing. Multiple bids can be placed on the same listing
    by the same or different companies.
    """

    __tablename__ = 'bids'

    # id, created_at and deleted_at are set automatically via BaseEntity

    listing_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('listings.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    bidder_company_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('companies.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    bidder_user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )

    amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    status: Mapped[BidStatus] = mapped_column(
        Enum(BidStatus, name='bid_status'),
        nullable=False,
        default=BidStatus.PENDING,
        index=True,
    )

    # Relationships
    listing: Mapped['Listing'] = relationship(
        'Listing',
        back_populates='bids',
    )

    bidder_company: Mapped['Company'] = relationship(
        'Company',
        back_populates='bids',
    )

    bidder_user: Mapped['User'] = relationship(
        'User',
        back_populates='bids',
    )
