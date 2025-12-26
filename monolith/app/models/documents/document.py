"""
Document ORM model
Represents a document reference
"""

from datetime import datetime

from app.models.base import Base, BaseEntity
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Document(Base, BaseEntity):
    """
    Meta-object to a file in a file system
    """

    __tablename__ = 'documents'

    # id, created_at and deleted_at are setted automatically
    internal_filename: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    mime: Mapped[str] = mapped_column(String(64), nullable=False)

    # Internal Access fields
    storage_bucket: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_object_key: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )

    # Audit fields
    created_by: Mapped[str] = mapped_column(
        ForeignKey('users.id'), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    instrument_documents: Mapped[list['InstrumentDocument']] = relationship(
        'InstrumentDocument',
        back_populates='document',
        cascade='all, delete-orphan',
    )
