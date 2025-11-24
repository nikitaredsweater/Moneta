"""
v1 API routes
"""

from app import repositories as repo
from app import schemas
from app.dependencies import get_current_user
from app.enums import PermissionEntity as Entity
from app.enums import PermissionVerb as Verb
from app.routers.v1.endpoints.auth import auth_router
from app.routers.v1.endpoints.company import company_router
from app.routers.v1.endpoints.company_address import company_address_router
from app.routers.v1.endpoints.document import document_router
from app.routers.v1.endpoints.instrument import instrument_router
from app.routers.v1.endpoints.mongo_db_tests import test_router
from app.routers.v1.endpoints.user import user_router
from app.security import Permission, has_permission, verify_password
from app.security.jwt import create_access_token
from fastapi import APIRouter, Depends

v1_router = APIRouter()

v1_router.include_router(user_router, prefix='/user')
v1_router.include_router(company_router, prefix='/company')
v1_router.include_router(company_address_router, prefix='/company-address')
v1_router.include_router(instrument_router, prefix='/instrument')
v1_router.include_router(auth_router, prefix='/auth')
v1_router.include_router(document_router, prefix='/document')
v1_router.include_router(test_router, prefix='/mongo')  # TODO: Remove


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


@v1_router.post('/sample-token')
async def make_key(user_login: schemas.UserLogin, user_repo: repo.User):
    # In a sense, this function is equivalent to login route.
    # It is just for testing pusposes.
    #
    # In the future, feel free to move this logic into an appropriate
    # router handler
    # TODO: Add validation of the user data
    user = await user_repo.get_by_email_exact(user_login.email)
    if user is None:
        raise Exception('no user found aaaaaa')

    if not verify_password(
        password=user_login.password, hashed_password=user.password
    ):
        raise Exception('Wrong Credentials')

    user_id = user.id
    token = create_access_token(user_id=user_id)
    return {'access_token': token, 'token_type': 'bearer'}


@v1_router.get('/me', response_model=schemas.User)
async def get_me(current_user=Depends(get_current_user)):
    return current_user
