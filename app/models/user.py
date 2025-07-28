"""
User ORM model
"""

from sqlalchemy import Enum, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.enums import UserRole
from app.models.base import Base, BaseEntity


class User(Base, BaseEntity):
    """
    User profile
    """

    __tablename__ = 'users'

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.BUYER,
        server_default=text("'BUYER'"),
    )

    # TODO: Add a Alembic migration after merging with other branches
