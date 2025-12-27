"""
Ask ORM model
Represents an asking price set by the listing owner for their listed instrument.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from app.enums import AskStatus, ExecutionMode
from app.models.base import Base, BaseEntity
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.listing import Listing
    from app.models.user import User


class Ask(Base, BaseEntity):
    """
    Ask price on a listing.

    Represents an asking price set by the company that owns the listing.
    The asker company must be the same as the listing's seller company.
    Multiple asks can exist for the same listing.
    """

    __tablename__ = 'asks'

    # id, created_at and deleted_at are set automatically via BaseEntity

    listing_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('listings.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    asker_company_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('companies.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    asker_user_id: Mapped[UUID] = mapped_column(
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

    execution_mode: Mapped[ExecutionMode] = mapped_column(
        Enum(ExecutionMode, name='execution_mode'),
        nullable=False,
        default=ExecutionMode.MANUAL,
    )

    binding: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    status: Mapped[AskStatus] = mapped_column(
        Enum(AskStatus, name='ask_status'),
        nullable=False,
        default=AskStatus.ACTIVE,
        index=True,
    )

    # Relationships
    listing: Mapped['Listing'] = relationship(
        'Listing',
        back_populates='asks',
    )

    asker_company: Mapped['Company'] = relationship(
        'Company',
        back_populates='asks',
    )

    asker_user: Mapped['User'] = relationship(
        'User',
        back_populates='asks',
    )
