"""
InstrumentOwnership ORM model
Stores ownership change history for instruments.
Each record represents an owner of an instrument and the period of ownership.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from app.enums import AcquisitionReason
from app.models.base import Base, BaseEntity
from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.instrument import Instrument


class InstrumentOwnership(Base, BaseEntity):
    """
    Ownership history for instruments.

    Key rules:
    - Records are never updated — only closed (relinquished_at set) and new ones inserted
    - At most one active row per (instrument, owner) combination
    - Active ownership has relinquished_at = NULL
    """

    __tablename__ = 'instrument_ownerships'

    # id, created_at and deleted_at are set automatically via BaseEntity

    instrument_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('instruments.id', ondelete='CASCADE'),
        nullable=False,
    )

    owner_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('companies.id', ondelete='CASCADE'),
        nullable=False,
    )

    acquired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    relinquished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    acquisition_reason: Mapped[AcquisitionReason] = mapped_column(
        Enum(AcquisitionReason, name='acquisition_reason'),
        nullable=False,
        default=AcquisitionReason.ISSUANCE,
    )

    # Relationships
    instrument: Mapped['Instrument'] = relationship(
        'Instrument',
        back_populates='ownerships',
    )

    owner: Mapped['Company'] = relationship(
        'Company',
        back_populates='instrument_ownerships',
    )
