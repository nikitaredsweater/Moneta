"""
Dependencies module
"""

from typing import Generator, Optional, Set
from uuid import UUID

from app.enums import CompanyInclude
from app.repositories.user import User
from app.security.jwt import verify_access_token
from app.utils.minio_client import minio_client
from fastapi import HTTPException, Query, Request, status
from jose import JWTError
from minio import Minio


async def get_current_user(request: Request) -> object:
    """
    Gets user from request state (set by middleware or other dependencies).

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        object: The user object from request state.

    Raises:
        HTTPException: 401 Unauthorized if user is not found in state.
    """
    user = getattr(request.state, 'user', None)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='User not found in request state',
        )
    return user


async def get_current_user_from_token(
    request: Request, user_repo: User
) -> object:
    """
    Parses JWT token, fetches user from database,
    and sets user to request state.

    Args:
        request (Request): The incoming HTTP request containing
                the Authorization header.
        user_repo (UserRepository): Repository for user operations.

    Returns:
        object: The authenticated user object from database.

    Raises:
        HTTPException:
            - 401 Unauthorized if Authorization header is missing or doesn't
                    start with 'Bearer '
            - 401 Unauthorized if the JWT token is invalid,
                    expired, or malformed
            - 401 Unauthorized if user is not found in database
    """
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Missing or malformed Authorization header',
        )

    token = auth.split(' ')[1]
    try:
        payload = verify_access_token(token)
        user_id_str = payload.get('sub')
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Token missing subject (sub)',
            )

        # Parse UUID and fetch user from database
        user_id = UUID(user_id_str)
        user = await user_repo.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='User not found',
            )

        # Set user to request state for future use
        request.state.user = user

        return user

    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid or expired token',
        )


def get_minio_client() -> Generator[Minio, None, None]:
    """
    FastAPI-compatible dependency that returns the shared MinIO client.

    Yields:
        Minio: A MinIO client session.
    """
    yield minio_client


def parse_company_includes(
    include: Optional[str] = Query(
        None,
        description="Comma-separated list of related entities to include. "
        "Allowed: addresses,users,instruments",
    ),
) -> Set[CompanyInclude]:
    """
    Set of additional entities that a user requested to be retrieved with
    every company they are searching
    """
    if not include:
        return set()

    raw_parts = [
        part.strip().lower() for part in include.split(",") if part.strip()
    ]
    includes: Set[CompanyInclude] = set()

    mapping = {
        "addresses": CompanyInclude.ADDRESSES,
        "users": CompanyInclude.USERS,
        "instruments": CompanyInclude.INSTRUMENTS,
    }

    for part in raw_parts:
        if part in mapping:
            includes.add(mapping[part])
        # silently ignore unknown values, or raise HTTPException if you prefer

    return includes
