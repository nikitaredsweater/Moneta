"""
A sub-entity of the comapny
"""

from app.enums import AddressType
from app.models.base import Base, BaseEntity
from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class CompanyAddress(Base, BaseEntity):
    """
    Represents an address associated with a company.
    """

    __tablename__ = 'company_addresses'

    company_id: Mapped[int] = mapped_column(
        ForeignKey('companies.id', ondelete='CASCADE'), nullable=False
    )
    type: Mapped[AddressType] = mapped_column(Enum(AddressType), nullable=False)

    street: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(
        String(2), nullable=False
    )  # ISO 3166-1 alpha-2

    company = relationship('Company', back_populates='addresses')
