"""
v1 API routes
"""

from fastapi import APIRouter

v1_router = APIRouter()


@v1_router.get('/')
async def root() -> dict[str, str]:
    """
    Test endpoint.

    Returns:
        dict[str, str]: A dictionary with a message key and value.
    """
    return {'message': 'Hello World'}
