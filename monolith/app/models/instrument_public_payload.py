"""
ORM model for public non-uniform instrument representaions.

Represents JSON object that is used for NFT hashing.
"""
from typing import Any, Dict

from app.models.base import Base, BaseEntity
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


class InstrumentPublicPayload(Base, BaseEntity):
    """
    Public payload for an instrument.

    Stores non-uniform, public-facing data for an instrument
    (what the outside world / UI sees).
    """

    __tablename__ = "instrument_public_payloads"

    instrument_id: Mapped[str] = mapped_column(
        ForeignKey("instruments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # 1–1 with Instrument
    )

    # Arbitrary JSON payload for public fields
    payload: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # --- Relationships ---

    instrument: Mapped["Instrument"] = relationship(
        "Instrument",
        back_populates="public_payload",
        uselist=False,
    )