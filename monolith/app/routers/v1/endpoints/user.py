"""
User endpoints
"""

import logging
from typing import List, Optional

from app.utils import validations

logger = logging.getLogger(__name__)

from app import repositories as repo
from app import schemas
from app.dependencies import get_current_user
from app.enums import PermissionEntity as Entity
from app.enums import PermissionVerb as Verb
from app.exceptions import (
    EntityAlreadyExistsException,
    FailedToCreateEntityException,
    ForbiddenException,
    WasNotFoundException,
)
from app.security import (
    Permission,
    encrypt_password,
    has_permission,
)
from app.utils.filters.user_filters import build_sort_user, build_where_user
from fastapi import APIRouter, Depends

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
    logger.debug('[BUSINESS] Fetching all users')
    users = await user_repo.get_all()
    logger.info('[BUSINESS] Users retrieved | count=%d', len(users))
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
    logger.debug(
        '[BUSINESS] Searching users | limit=%d | offset=%d',
        filters.limit,
        filters.offset,
    )
    where = build_where_user(filters)
    order_list = build_sort_user(filters.sort)

    users = await user_repo.get_all(
        where_list=where or None,
        order_list=order_list or None,
        limit=filters.limit,
        offset=filters.offset,
    )
    logger.info('[BUSINESS] User search completed | results=%d', len(users))
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
    logger.debug('[BUSINESS] Fetching user | user_id=%s', user_id)
    user_found = None
    try:
        user_found = await user_repo.get_by_id(user_id)
    except Exception as e:
        logger.error(
            '[BUSINESS] Exception finding user | user_id=%s | error_type=%s | '
            'error=%s',
            user_id,
            type(e).__name__,
            str(e),
        )
    if user_found:
        logger.info('[BUSINESS] User retrieved | user_id=%s', user_id)
    else:
        logger.warning('[BUSINESS] User not found | user_id=%s', user_id)
    return user_found


@user_router.delete('/{user_id}', response_model=schemas.User)
async def delete_user(
    user_id: schemas.MonetaID,
    user_repo: repo.User,
    current_user=Depends(get_current_user),
    _=Depends(has_permission([Permission(Verb.DELETE, Entity.USER)])),
) -> schemas.User:
    """
    Current implementation simply deletes a user from the database, given that
    the user requesting this action shares the same company id as that account
    who they are trying to delete.

    Args:
        user_id (schemas.MonetaID): Valid uuid4 ID
        user_repo (repo.User): dependency injection of the User Repository
        current_user: Current User

    Returns:
        UserSchema: The deleted user object
    """
    logger.debug(
        '[BUSINESS] Deleting user | user_id=%s | requested_by=%s',
        user_id,
        current_user.id,
    )
    # Validations
    user_to_delete = None
    try:
        user_to_delete = await user_repo.get_by_id(user_id)
    except Exception as e:
        logger.warning('[BUSINESS] User not found for deletion | user_id=%s', user_id)
        raise WasNotFoundException  # 404

    if user_to_delete is None:
        logger.warning('[BUSINESS] User not found for deletion | user_id=%s', user_id)
        raise WasNotFoundException  # 404

    if user_to_delete.company_id:
        # Only same company user can delete a user
        if current_user.company_id != user_to_delete.company_id:
            logger.warning(
                '[BUSINESS] Forbidden delete attempt | user_id=%s | '
                'requester_company=%s | target_company=%s',
                user_id,
                current_user.company_id,
                user_to_delete.company_id,
            )
            raise ForbiddenException  # 403
    else:
        logger.warning(
            '[BUSINESS] User has no company, cannot delete | user_id=%s', user_id
        )
        raise WasNotFoundException  # 404

    # Deleting
    user_to_delete = await user_repo.delete_by_id(user_id)
    logger.info(
        '[BUSINESS] User deleted | user_id=%s | deleted_by=%s',
        user_id,
        current_user.id,
    )
    return user_to_delete  # Entity that was deleted

@user_router.patch("/{user_id}", response_model=schemas.User)
async def patch_user(
    user_id: schemas.MonetaID,
    user_repo: repo.User,
    user_patch_data: schemas.UserPatch,
    current_user=Depends(get_current_user),
    _=Depends(has_permission([Permission(Verb.UPDATE, Entity.USER)])),
):
    """
    Update some user parameters. Pass the parameters that you would like to
    update inside of the body of the request.

    Only users from the same company can perform this action.
    """
    logger.debug(
        '[BUSINESS] Patching user | user_id=%s | requested_by=%s',
        user_id,
        current_user.id,
    )
    user_to_patch = None
    try:
        user_to_patch = await user_repo.get_by_id(user_id)
    except Exception as e:
        logger.warning('[BUSINESS] User not found for patch | user_id=%s', user_id)
        raise WasNotFoundException  # 404

    if user_to_patch is None:
        logger.warning('[BUSINESS] User not found for patch | user_id=%s', user_id)
        raise WasNotFoundException  # 404

    if user_to_patch.company_id:
        # Only same company user can patch a user
        if current_user.company_id != user_to_patch.company_id:
            logger.warning(
                '[BUSINESS] Forbidden patch attempt | user_id=%s | '
                'requester_company=%s | target_company=%s',
                user_id,
                current_user.company_id,
                user_to_patch.company_id,
            )
            raise ForbiddenException  # 403
    else:
        logger.warning(
            '[BUSINESS] User has no company, cannot patch | user_id=%s', user_id
        )
        raise WasNotFoundException  # 404

    # Checking the data passed
    if user_patch_data.email:
        # Check email is valid format
        validations.ensure_valid_email(user_patch_data.email, 'email')  # 422
        # Check that email is not taken
        existing_user = await user_repo.get_by_email_exact(user_patch_data.email)
        if existing_user:
            logger.warning(
                '[BUSINESS] Email already exists | user_id=%s | email=%s',
                user_id,
                user_patch_data.email,
            )
            raise EntityAlreadyExistsException  # 409

    if user_patch_data.first_name:
        validations.ensure_not_empty(user_patch_data.first_name, 'first_name')  # 422

    if user_patch_data.last_name:
        validations.ensure_not_empty(user_patch_data.last_name, 'last_name')  # 422

    # Main logic
    updated = await user_repo.update_by_id(user_id, user_patch_data)
    logger.info(
        '[BUSINESS] User patched | user_id=%s | patched_by=%s',
        user_id,
        current_user.id,
    )
    return updated

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
    logger.debug(
        '[BUSINESS] Creating user | email=%s | company_id=%s',
        user_data.email,
        getattr(user_data, 'company_id', None),
    )
    # Validations
    if hasattr(user_data, 'company_id') and user_data.company_id:
        company = await company_repo.get_by_id(user_data.company_id)
        if not company:
            logger.warning(
                '[BUSINESS] Company not found for user creation | company_id=%s',
                user_data.company_id,
            )
            raise WasNotFoundException(
                detail=f'Company with ID {user_data.company_id} does not exist'
            )

    existing_user = await user_repo.get_by_email_exact(user_data.email)
    if existing_user:
        logger.warning(
            '[BUSINESS] User already exists with email | email=%s', user_data.email
        )
        raise EntityAlreadyExistsException

    # Main logic
    user_data.password = encrypt_password(user_data.password)

    try:
        user = await user_repo.create(user_data)
        logger.info(
            '[BUSINESS] User created | user_id=%s | email=%s',
            user.id,
            user.email,
        )
        return user
    except Exception as e:
        logger.error(
            '[BUSINESS] Failed to create user | email=%s | error_type=%s | error=%s',
            user_data.email,
            type(e).__name__,
            str(e),
        )
        raise FailedToCreateEntityException
