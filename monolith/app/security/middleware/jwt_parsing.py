"""
Middleware module for JWT parsing and setting `request.state.user`.

This middleware authenticates incoming requests using JWT tokens and
loads the associated user object from the database. If valid, the
user is attached to the request state for downstream access.
"""

import fnmatch
from uuid import UUID

from fastapi import status
from jose import JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.repositories.user import UserRepository
from app.security.jwt import verify_access_token
from app.utils.session import async_session

# TODO: Set /* to /
EXCLUDED_PATH_PATTERNS = ['/*', '/v1/sample-token', '/openapi.json', '/docs']


def _is_path_excluded(path: str) -> bool:
    """
    Determines whether a given path should be excluded from authentication.

    Args:
        path (str): The request path.

    Returns:
        bool: True if the path is excluded from JWT authentication.
    """
    for pattern in EXCLUDED_PATH_PATTERNS:
        if fnmatch.fnmatch(path, pattern):
            return True
    return False


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to authenticate requests using JWT tokens.

    If a request includes a valid JWT in the `Authorization` header, the
    associated user is fetched from the database and stored in `request.state.user`.

    Requests to excluded paths bypass authentication.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Processes each incoming request.

        Verifies the JWT token, fetches the corresponding user, and stores the
        user object in `request.state.user`. If the token is invalid or missing,
        returns a 401 Unauthorized response. Bypasses paths marked as excluded.

        Args:
            request (Request): The incoming HTTP request.
            call_next (Callable): The next middleware or endpoint handler.

        Returns:
            Response: The HTTP response after processing or early rejection.
        """
        if _is_path_excluded(request.url.path):
            return await call_next(request)

        auth = request.headers.get('Authorization')
        if not auth or not auth.startswith('Bearer '):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={'detail': 'Missing or malformed Authorization header'},
            )

        token = auth.split(' ')[1]
        try:
            payload = verify_access_token(token)
            user_id_str = payload.get('sub')
            if not user_id_str:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={'detail': 'Token missing subject (sub)'},
                )

            user_id = UUID(user_id_str)
            user_repo = UserRepository(async_session)
            user = await user_repo.get_by_id(user_id)
            if not user:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={'detail': 'User not found'},
                )

            # Attach full user object to request.state
            request.state.user = user

            return await call_next(request)

        except (JWTError, ValueError):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={'detail': 'Invalid or expired token'},
            )
        except Exception:
            # Add general exception handling for database issues
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={'detail': 'Internal server error'},
            )
