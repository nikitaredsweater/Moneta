"""
User DTOs
"""

from app.schemas.base import BaseDTO, CamelModel, MonetaID


class User(BaseDTO):
    """
    User profile
    """

    email: str
    first_name: str
    last_name: str
    company_id: MonetaID


class UserCreate(CamelModel):
    """
    User creation
    """

    email: str
    first_name: str
    last_name: str
    password: str
    company_id: MonetaID


class UserUpdate(CamelModel):
    """
    User update
    """

    email: str
    first_name: str
    last_name: str
    password: str


class UserDelete(CamelModel):
    """
    User deletion
    """
