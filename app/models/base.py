"""
Base model that can be used to inherit from.
"""

from uuid import uuid4

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base, declared_attr

Base = declarative_base()


class BaseID:

    @declared_attr
    def id(self) -> Column:
        return Column(UUID(as_uuid=True), default=uuid4, primary_key=True)


class BaseEntity(BaseID):  # pylint: disable=too-few-public-methods
    """Base ORM entity"""

    # TODO: Check if this is correct
    @declared_attr
    def created_at(self) -> Column:
        return Column(
            DateTime(timezone=True),
            default=func.current_timestamp(),  # pylint: disable=not-callable
            nullable=False,
            index=True,
        )

    @declared_attr
    def deleted_at(self) -> Column:
        return Column(DateTime(timezone=True), nullable=True, index=True)
