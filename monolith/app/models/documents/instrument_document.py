"""
InstrumentDocument ORM model
Association table that maps instruments with related documents.
Each instrument can have multiple documents, and each document can
relate to multiple instruments.
"""

from app.models.base import Base, BaseEntity
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class InstrumentDocument(Base, BaseEntity):
    """
    Association table between Instrument and Document.
    Represents a many-to-many relationship between instruments and documents.
    """

    __tablename__ = 'instrument_documents'

    # id, created_at and deleted_at are set automatically via BaseEntity

    instrument_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('instruments.id', ondelete='CASCADE'),
        nullable=False,
    )

    document_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('documents.id', ondelete='CASCADE'),
        nullable=False,
    )

    # Relationships
    instrument: Mapped['Instrument'] = relationship(
        'Instrument',
        back_populates='instrument_documents',
    )

    document: Mapped['Document'] = relationship(
        'Document',
        back_populates='instrument_documents',
    )
