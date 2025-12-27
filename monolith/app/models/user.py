"""
User ORM model
"""

from app.enums import UserRole, ActivationStatus
from app.models.base import Base, BaseEntity
from sqlalchemy import Enum, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship


class User(Base, BaseEntity):
    """
    User profile
    """

    __tablename__ = 'users'

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company_id: Mapped[int] = mapped_column(
        ForeignKey('companies.id'), nullable=False
    )
    company: Mapped['Company'] = relationship(back_populates='users')
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.BUYER,
        server_default=text("'BUYER'"),
    )
    account_status: Mapped[ActivationStatus] = mapped_column(
        Enum(ActivationStatus, name="account_status"),
        nullable=False,
        default=ActivationStatus.AWAITING_APPROVAL,
    )
    instruments: Mapped[list['Instrument']] = relationship(
        back_populates='creator', cascade='all, delete-orphan'
    )

    listings: Mapped[list['Listing']] = relationship(
        'Listing',
        back_populates='listing_creator',
        cascade='all, delete-orphan',
    )

    bids: Mapped[list['Bid']] = relationship(
        'Bid',
        back_populates='bidder_user',
        cascade='all, delete-orphan',
    )
