"""
v1 API routes
"""

from fastapi import APIRouter, Depends

from app import repositories as repo
from app import schemas
from app.dependencies import get_current_user
from app.enums import PermissionEntity as Entity
from app.enums import PermissionVerb as Verb
from app.routers.v1.endpoints.auth import auth_router
from app.routers.v1.endpoints.company import company_router
from app.routers.v1.endpoints.company_address import company_address_router
from app.routers.v1.endpoints.user import user_router
from app.security import Permission, has_permission, verify_password
from app.security.jwt import create_access_token

v1_router = APIRouter()

v1_router.include_router(user_router, prefix='/user')
v1_router.include_router(company_router, prefix='/company')
v1_router.include_router(company_address_router, prefix='/company-address')
v1_router.include_router(auth_router, prefix='/auth')


VIEW_ALL_DATA_PERMISSION = has_permission(
    [Permission(Verb.VIEW, Entity.COMPANY)]
)


# Test endpoint -- Remove in the future
@v1_router.get('/')
async def root(_=Depends(VIEW_ALL_DATA_PERMISSION)) -> dict[str, str]:
    """
    Test endpoint.

    Returns:
        dict[str, str]: A dictionary with a message key and value.
    """
    return {'message': 'Hello World'}


@v1_router.get('/me')
async def get_me(current_user=Depends(get_current_user)):
    return current_user
