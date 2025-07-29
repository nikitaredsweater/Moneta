"""
v1 API routes
"""

from fastapi import APIRouter, Depends

from app.enums import PermissionEntity as Entity
from app.enums import PermissionVerb as Verb
from app.routers.v1.endpoints.company import company_router
from app.routers.v1.endpoints.company_address import company_address_router
from app.routers.v1.endpoints.user import user_router
from app.security.permissions import Permission, has_permission

v1_router = APIRouter()

v1_router.include_router(user_router, prefix='/user')
v1_router.include_router(company_router, prefix='/company')
v1_router.include_router(company_address_router, prefix='/company-address')


VIEW_ALL_DATA_PERMISSION = has_permission([Permission(Verb.VIEW, Entity.ALL_DATA)])

# Test endpoint -- Remove in the future
@v1_router.get('/')
async def root(
    _=Depends(VIEW_ALL_DATA_PERMISSION)
) -> dict[str, str]:
    """
    Test endpoint.

    Returns:
        dict[str, str]: A dictionary with a message key and value.
    """
    return {'message': 'Only VIEW_ALL_DATA will see it'}
