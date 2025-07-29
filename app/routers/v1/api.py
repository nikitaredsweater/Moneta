"""
v1 API routes
"""

from fastapi import APIRouter

from app.routers.v1.endpoints.company import company_router
from app.routers.v1.endpoints.company_address import company_address_router
from app.routers.v1.endpoints.user import user_router

v1_router = APIRouter()

v1_router.include_router(user_router, prefix='/user')
v1_router.include_router(company_router, prefix='/company')
v1_router.include_router(company_address_router, prefix='/company-address')


# Test endpoint -- Remove in the future
@v1_router.get('/')
async def root() -> dict[str, str]:
    """
    Test endpoint.

    Returns:
        dict[str, str]: A dictionary with a message key and value.
    """
    return {'message': 'Hello World'}
