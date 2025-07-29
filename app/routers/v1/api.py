"""
v1 API routes
"""

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.routers.v1.endpoints.user import user_router
from app.security.jwt import create_access_token

v1_router = APIRouter()

v1_router.include_router(user_router, prefix='/user')


# Test endpoint -- Remove in the future
@v1_router.get('/')
async def root() -> dict[str, str]:
    """
    Test endpoint.

    Returns:
        dict[str, str]: A dictionary with a message key and value.
    """
    return {'message': 'Hello World'}


@v1_router.get('/sample-token')
async def make_key():
    token = create_access_token(user_id='user.id')
    return {'access_token': token, 'token_type': 'bearer'}


@v1_router.get('/me')
async def get_me(user_id=Depends(get_current_user)):
    return user_id
