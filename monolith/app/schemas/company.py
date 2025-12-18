"""
Company DTOs
"""

from datetime import date
from typing import List, Optional

from app.schemas.base import BaseDTO, CamelModel
from app.schemas.company_address import CompanyAddress
from app.schemas.instrument import Instrument
from app.schemas.user import User


class Company(BaseDTO):
    """
    Company profile
    """

    legal_name: str
    trade_name: str
    registration_number: str
    incorporation_date: date


class CompanyIncludes(Company):
    """
    Return model for optional including of some predefined entities that
    relate to the mother company entity through the id field
    """

    addresses: Optional[List[CompanyAddress]] = None
    users: Optional[List[User]] = None
    instruments: Optional[List[Instrument]] = None


class CompanyCreate(CamelModel):
    """
    Company profile
    """

    legal_name: str
    trade_name: str
    registration_number: str
    incorporation_date: date


class CompanyFilters(CamelModel):
    """
    Search parameters for Companies.
    All fields optional; send {} for default page.
    """

    # partial text matches
    legal_name: Optional[str] = None
    trade_name: Optional[str] = None
    registration_number: Optional[str] = None

    # date ranges
    incorporation_date_after: Optional[date] = None
    incorporation_date_before: Optional[date] = None
    created_at_after: Optional[date] = None
    created_at_before: Optional[date] = None

    # sorting & pagination
    # e.g. "-created_at,legal_name"
    sort: Optional[str] = "-created_at"
    limit: int = 50  # 1..200 enforced in repo if you like
    offset: int = 0
