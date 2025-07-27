"""
DTO
Schemas entrypoint.

You can import entities from here as schemas.User to avoid collision
with models module.
"""

from app.schemas.company import Company, CompanyCreate
from app.schemas.user import User, UserCreate, UserDelete, UserUpdate

__all__ = [
    'User',
    'UserCreate',
    'UserUpdate',
    'UserDelete',
    'Company',
    'CompanyCreate',
]
