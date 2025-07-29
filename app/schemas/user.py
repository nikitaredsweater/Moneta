"""
User DTOs
"""

from app.schemas.base import BaseDTO, CamelModel


class User(BaseDTO):
    """
    User profile
    """

    email: str
    first_name: str
    last_name: str


class UserCreate(BaseDTO):
    """
    User creation
    """

    email: str
    first_name: str
    last_name: str
    password: str


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


class UserLogin(CamelModel):
    """
    Used to login user and generate them JWT token
    """

    password: str
    email: str
