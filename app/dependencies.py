"""
Dependencies module
"""

from fastapi import HTTPException, Request, status
from jose import JWTError

from app.security.jwt import verify_access_token


async def get_current_user(request: Request) -> str:
    """
    Extracts and verifies JWT token from Authorization header to authenticate
    the current user.

    Expects an Authorization header in the format: "Bearer <jwt_token>"

    Args:
        request (Request): The incoming HTTP request containing the Authorization header.

    Returns:
        str: The authenticated user's ID extracted from the JWT token.

    Raises:
        HTTPException:
            - 401 Unauthorized if Authorization header is missing or
                doesn't start with 'Bearer '
            - 401 Unauthorized if the JWT token is
                invalid, expired, or malformed

    Example:
        Used as a FastAPI dependency:
        ```python
        @app.get("/protected")
        async def protected_route(current_user: str=Depends(get_current_user)):
            return {"user_id": current_user.id}
        ```

    Note:
        Currently returns a hardcoded 'user_id' string.
        Should be updated to return the actual schema.user from the
        JWT token payload.
    """
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing token'
        )

    token = auth.split(' ')[1]
    print(token)
    try:
        verify_access_token(token)
        return 'user_id'

    except JWTError:
        raise HTTPException(status_code=401, detail='Invalid or expired token')
