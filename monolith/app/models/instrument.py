"""
Instrument ORM model
Represents a debt-proven security that is traded on the platform.
Primarily represents a metadata, which is useful for platform users,
though the main trade takes place on the chain.
"""

from datetime import date, datetime

from app.enums import InstrumentStatus, MaturityStatus, TradingStatus
from app.models.base import Base, BaseEntity
from sqlalchemy import Date, Double
from sqlalchemy import Enum as PgEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Instrument(Base, BaseEntity):
    """
    Debt-based financial instrument.
    """

    __tablename__ = 'instruments'

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    face_value: Mapped[float] = mapped_column(Double, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    maturity_date: Mapped[date] = mapped_column(Date, nullable=False)
    maturity_payment: Mapped[float] = mapped_column(Double, nullable=False)

    instrument_status: Mapped[InstrumentStatus] = mapped_column(
        PgEnum(InstrumentStatus, name="instrument_status"),
        nullable=False,
        default=InstrumentStatus.DRAFT,
    )

    maturity_status: Mapped[MaturityStatus] = mapped_column(
        PgEnum(MaturityStatus, name="maturity_status"),
        nullable=False,
        default=MaturityStatus.NOT_DUE,
    )

    trading_status: Mapped[TradingStatus] = mapped_column(
        PgEnum(TradingStatus, name="trading_status"),
        nullable=False,
        default=TradingStatus.OFF_MARKET,
    )

    issuer_id: Mapped[str] = mapped_column(
        ForeignKey('companies.id'), nullable=False
    )
    created_by: Mapped[str] = mapped_column(
        ForeignKey('users.id'), nullable=False
    )

    public_payload: Mapped['InstrumentPublicPayload'] = relationship(
        "InstrumentPublicPayload",
        back_populates="instrument",
        uselist=False,
        cascade="all, delete-orphan",
    )

    issuer: Mapped['Company'] = relationship(back_populates='instruments')
    creator: Mapped['User'] = relationship(back_populates='instruments')

    instrument_documents: Mapped[list['InstrumentDocument']] = relationship(
        'InstrumentDocument',
        back_populates='instrument',
        cascade='all, delete-orphan',
    )

    ownerships: Mapped[list['InstrumentOwnership']] = relationship(
        'InstrumentOwnership',
        back_populates='instrument',
        cascade='all, delete-orphan',
    )

    listings: Mapped[list['Listing']] = relationship(
        'Listing',
        back_populates='instrument',
        cascade='all, delete-orphan',
    )
