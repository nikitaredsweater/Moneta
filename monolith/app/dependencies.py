"""
Dependencies module
"""

from typing import Generator, Optional, Set
from uuid import UUID

from app.enums import (
    AskInclude,
    BidInclude,
    CompanyInclude,
    InstrumentInclude,
    ListingInclude,
)
from app.repositories.user import User
from app.utils.minio_client import minio_client
from fastapi import HTTPException, Query, Request, status
from jose import JWTError
from minio import Minio
from moneta_auth import verify_access_token


async def get_current_user(request: Request) -> object:
    """
    Gets user from request state (set by middleware or other dependencies).

    First checks for request.state.user (legacy middleware support).
    Falls back to creating a user-like object from token_claims (moneta_auth).

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        object: The user object from request state or token claims.

    Raises:
        HTTPException: 401 Unauthorized if user is not found in state.
    """
    # First check for legacy request.state.user
    user = getattr(request.state, 'user', None)
    if user is not None:
        return user

    # Fall back to creating user-like object from moneta_auth token_claims
    token_claims = getattr(request.state, 'token_claims', None)
    if token_claims is not None:
        from types import SimpleNamespace

        # Convert string IDs to UUIDs for proper comparison with database entities
        company_id = (
            UUID(token_claims.company_id) if token_claims.company_id else None
        )
        return SimpleNamespace(
            id=UUID(token_claims.user_id),
            role=token_claims.role,
            company_id=company_id,
            account_status=token_claims.account_status,
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='User not found in request state',
    )


async def get_current_user_from_token(
    request: Request, user_repo: User
) -> object:
    """
    Parses JWT token, fetches user from database,
    and sets user to request state.

    Note: This function fetches the full user from DB. For most use cases,
    the token claims set by JWTAuthMiddleware are sufficient.
    Use request.state.token_claims for claims-based access.

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
        # verify_access_token now returns TokenClaims object
        claims = verify_access_token(token)
        user_id_str = claims.user_id

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
        description='Comma-separated list of related entities to include. '
        'Allowed: addresses,users,instruments',
    ),
) -> Set[CompanyInclude]:
    """
    Set of additional entities that a user requested to be retrieved with
    every company they are searching
    """
    if not include:
        return set()

    raw_parts = [
        part.strip().lower() for part in include.split(',') if part.strip()
    ]
    includes: Set[CompanyInclude] = set()

    mapping = {
        'addresses': CompanyInclude.ADDRESSES,
        'users': CompanyInclude.USERS,
        'instruments': CompanyInclude.INSTRUMENTS,
    }

    for part in raw_parts:
        if part in mapping:
            includes.add(mapping[part])
        # silently ignore unknown values, or raise HTTPException if you prefer

    return includes


def parse_instrument_includes(
    include: Optional[str] = Query(
        None,
        description='Comma-separated list of related entities to include. '
        'Allowed: documents',
    ),
) -> Set[InstrumentInclude]:
    """
    Set of additional entities that a user requested to be retrieved with
    every instrument they are searching
    """
    if not include:
        return set()

    raw_parts = [
        part.strip().lower() for part in include.split(',') if part.strip()
    ]
    includes: Set[InstrumentInclude] = set()

    mapping = {
        'documents': InstrumentInclude.DOCUMENTS,
    }

    for part in raw_parts:
        if part in mapping:
            includes.add(mapping[part])
        # silently ignore unknown values, or raise HTTPException if you prefer

    return includes


def parse_listing_includes(
    include: Optional[str] = Query(
        None,
        description='Comma-separated list of related entities to include. '
        'Allowed: instrument',
    ),
) -> Set[ListingInclude]:
    """
    Set of additional entities that a user requested to be retrieved with
    every listing they are searching
    """
    if not include:
        return set()

    raw_parts = [
        part.strip().lower() for part in include.split(',') if part.strip()
    ]
    includes: Set[ListingInclude] = set()

    mapping = {
        'instrument': ListingInclude.INSTRUMENT,
    }

    for part in raw_parts:
        if part in mapping:
            includes.add(mapping[part])
        # silently ignore unknown values

    return includes


def parse_bid_includes(
    include: Optional[str] = Query(
        None,
        description='Comma-separated list of related entities to include. '
        'Allowed: listing',
    ),
) -> Set[BidInclude]:
    """
    Set of additional entities that a user requested to be retrieved with
    every bid they are searching
    """
    if not include:
        return set()

    raw_parts = [
        part.strip().lower() for part in include.split(',') if part.strip()
    ]
    includes: Set[BidInclude] = set()

    mapping = {
        'listing': BidInclude.LISTING,
    }

    for part in raw_parts:
        if part in mapping:
            includes.add(mapping[part])
        # silently ignore unknown values

    return includes


def parse_ask_includes(
    include: Optional[str] = Query(
        None,
        description='Comma-separated list of related entities to include. '
        'Allowed: listing',
    ),
) -> Set[AskInclude]:
    """
    Set of additional entities that a user requested to be retrieved with
    every ask they are searching
    """
    if not include:
        return set()

    raw_parts = [
        part.strip().lower() for part in include.split(',') if part.strip()
    ]
    includes: Set[AskInclude] = set()

    mapping = {
        'listing': AskInclude.LISTING,
    }

    for part in raw_parts:
        if part in mapping:
            includes.add(mapping[part])
        # silently ignore unknown values

    return includes
