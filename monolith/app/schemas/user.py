"""
User DTOs
"""

from datetime import date
from typing import Optional

from app.enums import ActivationStatus, UserRole
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
    account_status: ActivationStatus


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
    account_status: ActivationStatus


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


class UserFilters(CamelModel):
    """
    Search parameters for Users (pagination + sorting included).
    All fields are optional; unspecified filters are ignored.
    """

    # exact or partial fields
    email: Optional[str] = None  # partial match (ilike)
    first_name: Optional[str] = None  # partial match (ilike)
    last_name: Optional[str] = None  # partial match (ilike)

    # exact filters
    role: Optional[UserRole] = None
    company_id: Optional[MonetaID] = None  # exact company

    # created_at range (inclusive)
    created_at_after: Optional[date] = None
    created_at_before: Optional[date] = None

    # sorting & pagination
    # "-created_at,first_name" → desc(created_at), asc(first_name)
    sort: Optional[str] = '-created_at'
    limit: int = 50  # 1..200 in repo
    offset: int = 0  # 0..∞ (enforced in repo/DB)
