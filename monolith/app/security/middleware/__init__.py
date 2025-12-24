"""
Middleware module for security-related middleware.

Uses JWTAuthMiddleware from moneta-auth package for JWT verification.
"""

from app.security.middleware.jwt_parsing import JWTAuthMiddleware

__all__ = [
    'JWTAuthMiddleware',
]
