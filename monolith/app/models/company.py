"""
Company ORM model
Represents the legal financial institution that is registered on the platform.
"""

from datetime import date

from app.models.base import Base, BaseEntity
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Company(Base, BaseEntity):
    """
    Company profile
    """

    __tablename__ = 'companies'

    legal_name: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    trade_name: Mapped[str] = mapped_column(
        String(255), nullable=True
    )  # Trade name may not always exist
    registration_number: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True
    )
    addresses: Mapped[list['CompanyAddress']] = relationship(
        'CompanyAddress', back_populates='company', cascade='all, delete-orphan'
    )
    incorporation_date: Mapped[date] = mapped_column(nullable=False)
    users: Mapped[list['User']] = relationship(
        back_populates='company', cascade='all, delete-orphan'
    )
    instruments: Mapped[list['Instrument']] = relationship(
        back_populates='issuer', cascade='all, delete-orphan'
    )

    instrument_ownerships: Mapped[list['InstrumentOwnership']] = relationship(
        'InstrumentOwnership',
        back_populates='owner',
        cascade='all, delete-orphan',
    )

    listings: Mapped[list['Listing']] = relationship(
        'Listing',
        back_populates='seller_company',
        cascade='all, delete-orphan',
    )

    bids: Mapped[list['Bid']] = relationship(
        'Bid',
        back_populates='bidder_company',
        cascade='all, delete-orphan',
    )

    asks: Mapped[list['Ask']] = relationship(
        'Ask',
        back_populates='asker_company',
        cascade='all, delete-orphan',
    )
