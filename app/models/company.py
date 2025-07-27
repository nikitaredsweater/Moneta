"""
Company ORM model
Represents the legal financial institution that is registered on the platform.
"""

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BaseEntity


class Company(Base, BaseEntity):
    """
    Company profile
    """

    __tablename__ = 'companies'

    legal_name: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    trade_name: Mapped[str] = mapped_column(
        String(255), nullable=True
    )  # Trade name may not always exist
    country: Mapped[str] = mapped_column(
        String(2), nullable=False
    )  # ISO 3166-1 alpha-2 country code
    registration_number: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True
    )
    incorporation_date: Mapped[Date] = mapped_column(nullable=False)
