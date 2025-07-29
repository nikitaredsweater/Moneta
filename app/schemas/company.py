"""
Company DTOs
"""

from datetime import date

from app.schemas.base import BaseDTO, CamelModel


class Company(BaseDTO):
    """
    Company profile
    """

    legal_name: str
    trade_name: str
    registration_number: str
    incorporation_date: date


class CompanyCreate(CamelModel):
    """
    Company profile
    """

    legal_name: str
    trade_name: str
    registration_number: str
    incorporation_date: date
