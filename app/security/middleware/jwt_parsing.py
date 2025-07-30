"""
Middleware module for JWT parsing and setting `request.state.user_id`.

This middleware ensures that protected routes are only accessible
to clients providing a valid JWT access token in the `Authorization` header.

Excluded routes (defined by `EXCLUDED_PATH_PATTERNS`) bypass the JWT check.
"""

import fnmatch
from uuid import UUID

from fastapi import status
from jose import JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.security.jwt import verify_access_token

EXCLUDED_PATH_PATTERNS = ['/', '/v1/sample-token', '/openapi.json', '/docs']


def _is_path_excluded(path: str) -> bool:
    """
    Checks whether the request path matches any pattern in the exclusion list.

    Args:
        path (str): The request path to check.

    Returns:
        bool: True if the path should bypass authentication, False otherwise.
    """
    for pattern in EXCLUDED_PATH_PATTERNS:
        if fnmatch.fnmatch(path, pattern):
            return True
    return False


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and verify JWT tokens from the Authorization header.

    If a valid token is present, it sets `request.state.user_id`
    for downstream use. Requests to excluded paths bypass this check.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Processes incoming requests to validate the JWT and inject user ID.

        Args:
            request (Request): The incoming HTTP request.
            call_next (Callable): The next middleware or route handler.

        Returns:
            Response: The HTTP response after processing or an error response.
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
        print(token)
        try:
            payload = verify_access_token(token)
            user_id_str = payload.get('sub')

            # TODO: Pull the user by id from the db

            if not user_id_str:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={'detail': 'Token missing subject (sub)'},
                )

            # Set the user ID on the request.state for downstream usage
            request.state.user_id = UUID(user_id_str)
            return await call_next(request)

        except (JWTError, ValueError):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={'detail': 'Invalid or expired token'},
            )
