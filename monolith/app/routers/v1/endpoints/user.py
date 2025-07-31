"""
User endpoints
"""

from typing import List, Optional

from app import repositories as repo
from app import schemas

# Example usage
from app.security import encrypt_password, verify_password
from fastapi import APIRouter

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
    user_data.password = encrypt_password(user_data.password)
    user = await user_repo.create(user_data)
    return user
