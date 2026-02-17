"""
Following the SOLID principle, we are separating the logic of the repository
and its implementation.
"""

# TODO: Introduce a Base IRepository
from app.repositories.interfaces.interface_user import IUserRepository

__all__ = [
    'IUserRepository',
]
