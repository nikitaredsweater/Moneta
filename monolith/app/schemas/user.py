"""
User DTOs
"""

from app.enums import UserRole
from app.schemas.base import BaseDTO, CamelModel, MonetaID


class User(BaseDTO):
    """
    User profile
    """

    email: str
    first_name: str
    last_name: str
    company_id: MonetaID
    role: UserRole


class UserInternal(BaseDTO):
    """
    User Internal Datastructure
    """

    email: str
    password: str
    first_name: str
    last_name: str
    company_id: MonetaID
    role: UserRole


class UserCreate(CamelModel):
    """
    User creation
    """

    email: str
    first_name: str
    last_name: str
    password: str
    company_id: MonetaID
    role: UserRole


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


class UserLogin(CamelModel):
    """
    Used to login user and generate them JWT token
    """

    password: str
    email: str
