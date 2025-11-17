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


################################################################################
#                              ENTITY EXCPETIONS
################################################################################


class WasNotFoundException(BaseHTTPException):
    """
    Exception raised when an entity was not found.
    """

    status_code = status.HTTP_404_NOT_FOUND
    detail = 'Entity was not found'


class EntityAlreadyExistsException(BaseHTTPException):
    """
    Exception raised when an entity was not found.
    """

    status_code = status.HTTP_409_CONFLICT
    detail = 'Entity with such unique fields already exists'


class EmptyEntityException(BaseHTTPException):
    """
    Exception raised when an input entity does not have a single input field.
    """

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = 'Entity passed in is empty'


class IncorrectInputFormatException(BaseHTTPException):
    """
    Exception raised when an input entity has
    at least one field in an unsupported format.
    """

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = 'Entity passed in has an invalid field'


################################################################################
#                              AUTH EXCPETIONS
################################################################################


class InvalidCredentialsException(BaseHTTPException):
    """
    Exception raised when request has invalid credentials.
    """

    status_code = status.HTTP_401_UNAUTHORIZED
    detail = 'Invalid credentials'


class InsufficientPermissionsException(BaseHTTPException):
    """
    Excpetion raised when the user has no permission to access a given endpoint.
    """

    status_code = status.HTTP_403_FORBIDDEN
    detail = 'Insufficient permissions'


class AccountStatusException(BaseHTTPException):
    """
    Excpetion raised when the user account has no
    permission to perform cetain action.
    """

    status_code = status.HTTP_403_FORBIDDEN
    detail = 'Wrong account status'


################################################################################
#                              SERVER EXCPETIONS
################################################################################
class FailedToCreateEntityException(BaseHTTPException):
    """
    Excpetion raised when server was not able to add an entity to the database.
    """

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = 'Failed to save the entity'
