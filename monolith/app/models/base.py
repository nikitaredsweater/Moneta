"""
Base model that can be used to inherit from.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class BaseID:
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid4, primary_key=True
    )


class BaseEntity(BaseID):
    """Base ORM entity"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.current_timestamp(),  # [not-callable]
        nullable=False,
        index=True,
    )

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
