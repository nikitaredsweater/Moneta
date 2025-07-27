"""
Company DTOs
"""

from datetime import date

from app.schemas.base import BaseDTO


class Company(BaseDTO):
    """
    Company profile
    """

    legal_name: str
    trade_name: str
    country: str
    registration_number: str
    incorporation_date: date


class CompanyCreate(BaseDTO):
    """
    Company profile
    """

    legal_name: str
    trade_name: str
    country: str
    registration_number: str
    incorporation_date: date
