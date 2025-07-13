"""
Custom exceptions module.
"""

from typing import Optional

from fastapi import HTTPException, status


class BaseHTTPException(HTTPException):
    """
    Base HTTP exception class.
    """

    status_code: int = status.HTTP_400_BAD_REQUEST
    detail: str = ''

    def __init__(
        self, status_code: Optional[int] = None, detail: Optional[str] = None
    ):
        super().__init__(status_code or self.status_code, detail or self.detail)


# Example custom exception -- Currently unused.
class WasNotFoundException(BaseHTTPException):
    """
    Exception raised when an entity was not found.
    """

    status_code = status.HTTP_404_NOT_FOUND
    detail = 'Entity was not found'
