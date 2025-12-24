"""
Middleware module for JWT parsing and setting request state.

This middleware authenticates incoming requests using JWT tokens from moneta-auth.
Token claims are extracted and attached to request.state for downstream access.

No database access is required - all authorization data comes from JWT claims.
"""

import fnmatch
import logging
from types import SimpleNamespace

from jose import JWTError
from moneta_auth import verify_access_token, ActivationStatus
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

EXCLUDED_PATH_PATTERNS = ['/', '/v1/auth/login', '/openapi.json', '/docs']


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

    Uses moneta-auth package for token verification. Extracts claims from
    the JWT and attaches them to request.state. No database access required.

    Sets:
        - request.state.token_claims: Full TokenClaims object
        - request.state.user_id: User ID string
        - request.state.role: UserRole enum
        - request.state.company_id: Company ID string (or None)
        - request.state.user: SimpleNamespace for backward compatibility

    Requests to excluded paths bypass authentication.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Processes each incoming request.

        Verifies the JWT token, extracts claims, and attaches them to
        request.state. If the token is invalid or missing, returns a
        401 Unauthorized response. Bypasses paths marked as excluded.

        Args:
            request (Request): The incoming HTTP request.
            call_next (Callable): The next middleware or endpoint handler.

        Returns:
            Response: The HTTP response after processing or early rejection.
        """
        if _is_path_excluded(request.url.path):
            logger.debug('[AUTH] Path excluded from JWT auth | path=%s', request.url.path)
            return await call_next(request)

        auth = request.headers.get('Authorization')
        if not auth or not auth.startswith('Bearer '):
            logger.warning(
                '[AUTH] Missing or malformed Authorization header | path=%s',
                request.url.path,
            )
            return JSONResponse(
                status_code=401,
                content={'detail': 'Missing or malformed Authorization header'},
            )

        token = auth.split(' ')[1]
        try:
            # Verify token and get claims using moneta-auth
            claims = verify_access_token(token)

            # Check account status
            if claims.account_status != ActivationStatus.ACTIVE:
                logger.warning(
                    '[AUTH] Account not active | user_id=%s | status=%s | path=%s',
                    claims.user_id,
                    claims.account_status.value,
                    request.url.path,
                )
                return JSONResponse(
                    status_code=403,
                    content={'detail': f'Account is {claims.account_status.value.lower()}'},
                )

            # Attach claims to request.state (used by has_permission from moneta-auth)
            request.state.token_claims = claims

            # Convenience attributes
            request.state.user_id = claims.user_id
            request.state.role = claims.role
            request.state.company_id = claims.company_id

            # Backward compatibility: create a user-like object from claims
            # This allows existing code using request.state.user to continue working
            request.state.user = SimpleNamespace(
                id=claims.user_id,
                role=claims.role,
                company_id=claims.company_id,
                account_status=claims.account_status,
            )

            logger.debug(
                '[AUTH] User authenticated | user_id=%s | role=%s | path=%s',
                claims.user_id,
                claims.role.value,
                request.url.path,
            )

            return await call_next(request)

        except JWTError as e:
            logger.warning(
                '[AUTH] Invalid or expired token | path=%s | error=%s',
                request.url.path,
                str(e),
            )
            return JSONResponse(
                status_code=401,
                content={'detail': 'Invalid or expired token'},
            )
        except RuntimeError as e:
            # Key not loaded
            logger.error('[AUTH] JWT key not configured | error=%s', str(e))
            return JSONResponse(
                status_code=500,
                content={'detail': 'Authentication service misconfigured'},
            )
        except Exception as e:
            logger.error(
                '[AUTH] Internal server error during authentication | path=%s | '
                'error_type=%s | error=%s',
                request.url.path,
                type(e).__name__,
                str(e),
            )
            return JSONResponse(
                status_code=500,
                content={'detail': 'Internal server error'},
            )
