"""
User endpoints
"""

from fastapi import APIRouter

from app import schemas
from app import repositories as repo

user_router = APIRouter()


@user_router.get('/')
async def get_users(user_repo: repo.UserRepository):
    """
    Get user

    Returns:
        schemas.User: A user object.
    """
    users = await user_repo.get_all()
    return users

