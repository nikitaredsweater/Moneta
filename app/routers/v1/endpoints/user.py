"""
User endpoints
"""

from fastapi import APIRouter

from app import schemas

user_router = APIRouter()


@user_router.get('/')
async def get_user() -> schemas.User:
    """
    Get user

    Returns:
        schemas.User: A user object.
    """
    return schemas.User(
        email='test@test.com',
        first_name='John',
        last_name='Doe',
    )
