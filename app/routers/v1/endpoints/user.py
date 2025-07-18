"""
User endpoints
"""

from typing import List, Optional

from fastapi import APIRouter

from app import repositories as repo
from app import schemas

user_router = APIRouter()


@user_router.get('/', response_model=List[schemas.User])
async def get_users(user_repo: repo.User) -> Optional[List[schemas.User]]:
    """
    Get all users

    Args:
        user_repo (repo.User): dependency injection of the User Repository

    Returns:
        schemas.User: A user object.
    """
    users = await user_repo.get_all()
    return users


@user_router.post('/', response_model=schemas.User)
async def create_user(
    user_data: schemas.UserCreate, user_repo: repo.User
) -> schemas.User:
    """
    Create a new user

    Args:
        user_data: User creation data
        user_repo: User repository dependency

    Returns:
        UserSchema: The created user object
    """
    user = await user_repo.create(user_data)
    return user
