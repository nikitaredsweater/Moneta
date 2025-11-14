"""
User endpoints
"""

import logging
from typing import List, Optional

logger = logging.getLogger()

from app import repositories as repo
from app import schemas
from app.enums import PermissionEntity as Entity
from app.enums import PermissionVerb as Verb
from app.exceptions import (
    EntityAlreadyExistsException,
    FailedToCreateEntityException,
    WasNotFoundException,
)
from app.security import (
    Permission,
    encrypt_password,
    has_permission,
    verify_password,
)
from fastapi import APIRouter, Depends
from app.utils.filters.user_filters import (build_where_user, build_sort_user)

user_router = APIRouter()


@user_router.get('/', response_model=List[schemas.User])
async def get_all_users(
    user_repo: repo.User,
    _=Depends(has_permission([Permission(Verb.VIEW, Entity.ALL_USERS)])),
) -> Optional[List[schemas.User]]:
    """
    Get all users

    Args:
        user_repo (repo.User): dependency injection of the User Repository

    Returns:
        schemas.User: A user object.
    """
    users = await user_repo.get_all()
    return users

@user_router.post("/search", response_model=List[schemas.User])
async def search_users(
    user_repo: repo.User,
    filters: schemas.UserFilters,
    _=Depends(has_permission([Permission(Verb.VIEW, Entity.ALL_USERS)])),
) -> Optional[List[schemas.User]]:
    """
    Search users with pagination and sorting.
    Body: UserFilters (camelCase JSON).
    """
    where = build_where_user(filters)
    order_list = build_sort_user(filters.sort)

    users = await user_repo.get_all(
        where_list=where or None,
        order_list=order_list or None,
        limit=filters.limit,
        offset=filters.offset,
    )
    return users


@user_router.get('/{user_id}', response_model=Optional[schemas.User])
async def get_user_by_id(
    user_id: schemas.MonetaID,
    user_repo: repo.User,
    _=Depends(has_permission([Permission(Verb.VIEW, Entity.USER)])),
) -> Optional[schemas.User]:
    """
    Get a user by id

    Args:
        user_id (schemas.MonetaID): Valid uuid4 ID
        user_repo (repo.User): dependency injection of the User Repository

    Returns:
        Optional[schemas.User]: A user object.
    """
    user_found = None
    try:
        user_found = await user_repo.get_by_id(user_id)
    except Exception as e:
        logger.info('exception finding the user')
        logger.info(e)
    finally:
        return user_found


@user_router.post('/', response_model=schemas.User)
async def create_user(
    user_data: schemas.UserCreate,
    user_repo: repo.User,
    company_repo: repo.Company,
    _=Depends(has_permission([Permission(Verb.CREATE, Entity.USER)])),
) -> schemas.User:
    """
    Create a new user. Can only be used by users with CREATE_USER permission.

    Args:
        user_data: User creation data
        user_repo: User repository dependency

    Returns:
        UserSchema: The created user object
    """
    # Validations
    if hasattr(user_data, 'company_id') and user_data.company_id:
        company = await company_repo.get_by_id(user_data.company_id)
        if not company:
            raise WasNotFoundException(
                detail=f'Company with ID {user_data.company_id} does not exist'
            )

    existing_user = await user_repo.get_by_email_exact(user_data.email)
    if existing_user:
        raise EntityAlreadyExistsException

    # Main logic
    user_data.password = encrypt_password(user_data.password)

    try:
        user = await user_repo.create(user_data)
        return user
    except Exception:
        raise FailedToCreateEntityException
