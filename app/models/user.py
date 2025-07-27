"""
User ORM model
"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Company
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
    company_id: Mapped[int] = mapped_column(
        ForeignKey('companies.id'), nullable=False
    )
    company: Mapped['Company'] = relationship(back_populates='users')
