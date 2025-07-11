"""
User endpoints
"""

from fastapi import APIRouter

user_router = APIRouter()


@user_router.get('/')
async def get_user() -> dict[str, str]:
    """
    Get user

    Returns:
        dict[str, str]: A dictionary with a message key and value.
    """
    return {'message': 'User endpoint will be here one day'}
