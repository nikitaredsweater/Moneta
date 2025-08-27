"""
Document ORM model
Represents a document version reference
"""

from datetime import datetime

from app.models.base import Base, BaseEntity
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    UniqueConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column


class DocumentVersion(Base, BaseEntity):
    """
    Meta-object to a file in a file system
    """

    __tablename__ = 'document_versions'

    document_id: Mapped[str] = mapped_column(
        ForeignKey('documents.id'), nullable=False
    )
    version_number: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    storage_version_id: Mapped[str] = mapped_column(String)
    created_by: Mapped[str] = mapped_column(
        ForeignKey('users.id'), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    active: Mapped[bool] = mapped_column(
        Boolean, default=True
    )  # Set to False when version is deleted

    __table_args__ = (
        CheckConstraint(
            'version_number > 0', name='ck_version_number_positive'
        ),
        UniqueConstraint(
            "document_id",
            "version_number",
            name="uq_document_versions_doc_ver",
        ),
        UniqueConstraint(
            "document_id",
            "storage_version_id",
            name="uq_document_versions_doc_storage_ver",
        ),
    )
