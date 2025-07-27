"""
User DTOs
"""

from app.schemas.base import BaseDTO, MonetaID


class User(BaseDTO):
    """
    User profile
    """

    email: str
    first_name: str
    last_name: str
    company_id: MonetaID


class UserCreate(BaseDTO):
    """
    User creation
    """

    email: str
    first_name: str
    last_name: str
    password: str
    company_id: MonetaID


class UserUpdate(BaseDTO):
    """
    User update
    """

    email: str
    first_name: str
    last_name: str
    password: str


class UserDelete(BaseDTO):
    """
    User deletion
    """
