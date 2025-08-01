"""
User ORM model
"""

from app.enums import UserRole
from app.models.base import Base, BaseEntity
from sqlalchemy import Enum, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship


class User(Base, BaseEntity):
    """
    User profile
    """

    __tablename__ = 'users'

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company_id: Mapped[int] = mapped_column(
        ForeignKey('companies.id'), nullable=False
    )
    company: Mapped['Company'] = relationship(back_populates='users')
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.BUYER,
        server_default=text("'BUYER'"),
    )
    instruments: Mapped[list['Instrument']] = relationship(
    back_populates='creator', cascade='all, delete-orphan'
    )
