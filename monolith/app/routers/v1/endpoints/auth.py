"""
Authentication endpoints.

Provides routes for user login and token generation using JWT.
"""

from app import repositories as repo
from app import schemas
from app.exceptions import InvalidCredentialsException
from app.security import create_access_token, verify_password
from fastapi import APIRouter

auth_router = APIRouter()


@auth_router.post('/login')
async def get_jwt_token(
    user_repo: repo.User, user_login: schemas.UserLogin
) -> dict:
    """
    Authenticate a user and return a JWT access token.

    This endpoint verifies the provided credentials against the stored
    user data. If the credentials are valid, a signed JWT token is returned.

    Args:
        user_repo (UserRepository): The user repository
                                    for DB interaction (injected).
        user_login (schemas.UserLogin): Login credentials containing
                                    email and password.

    Returns:
        dict: A dictionary with the JWT token and token type
                (e.g. {"access_token": ..., "token_type": "bearer"}).

    Raises:
        InvalidCredentialsException:
            - If the user is not found by email.
            - If the password is incorrect.

    Example:
        ```json
        POST /login
        {
            "email": "user@example.com",
            "password": "password123"
        }

        Response:
        {
            "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer"
        }
        ```
    """
    user = await user_repo.get_by_email_exact(user_login.email)

    if user is None:
        raise InvalidCredentialsException

    if not verify_password(
        password=user_login.password, hashed_password=user.password
    ):
        raise InvalidCredentialsException

    token = create_access_token(user_id=user.id)
    return {'access_token': token, 'token_type': 'bearer'}
