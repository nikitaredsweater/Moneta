"""
Middleware module for application-wide middleware components.

Note: RequestLoggingMiddleware is now provided by the moneta_logging package.
Import it directly from moneta_logging.middleware.
"""

# Re-export for backward compatibility
from moneta_logging.middleware import RequestLoggingMiddleware

__all__ = [
    'RequestLoggingMiddleware',
]
