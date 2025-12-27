"""
Listing ORM model
Represents an instrument that is listed for trading on the platform.
"""

from typing import TYPE_CHECKING, List

from app.enums import ListingStatus
from app.models.base import Base, BaseEntity
from sqlalchemy import Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.bid import Bid
    from app.models.company import Company
    from app.models.instrument import Instrument
    from app.models.user import User


class Listing(Base, BaseEntity):
    """
    Listing for trading an instrument on the platform.

    Represents an instrument that the owner wants to sell.
    Only one OPEN listing can exist per instrument at a time.
    """

    __tablename__ = 'listings'

    # id, created_at and deleted_at are set automatically via BaseEntity

    instrument_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('instruments.id', ondelete='CASCADE'),
        nullable=False,
    )

    seller_company_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('companies.id', ondelete='CASCADE'),
        nullable=False,
    )

    listing_creator_user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )

    status: Mapped[ListingStatus] = mapped_column(
        Enum(ListingStatus, name='listing_status'),
        nullable=False,
        default=ListingStatus.OPEN,
    )

    # Relationships
    instrument: Mapped['Instrument'] = relationship(
        'Instrument',
        back_populates='listings',
    )

    seller_company: Mapped['Company'] = relationship(
        'Company',
        back_populates='listings',
    )

    listing_creator: Mapped['User'] = relationship(
        'User',
        back_populates='listings',
    )

    bids: Mapped[List['Bid']] = relationship(
        'Bid',
        back_populates='listing',
    )
