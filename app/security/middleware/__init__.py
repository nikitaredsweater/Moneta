"""
Middleware module for security-related middleware
"""

from app.security.middleware.jwt_parsing import JWTAuthMiddleware

__all__ = [
    'JWTAuthMiddleware',
]
