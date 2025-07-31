"""
Company Address DTOs
"""

from typing import Optional

from app.enums import AddressType
from app.schemas.base import BaseDTO, CamelModel, MonetaID


class CompanyAddress(BaseDTO):
    """
    Full company address DTO
    """

    type: AddressType
    street: str
    city: str
    state: Optional[str] = None
    postal_code: str
    country: str  # ISO 3166-1 alpha-2
    company_id: MonetaID


class CompanyAddressCreate(CamelModel):
    """
    DTO for creating a company address
    """

    type: AddressType
    street: str
    city: str
    state: Optional[str] = None
    postal_code: str
    country: str
    company_id: MonetaID
