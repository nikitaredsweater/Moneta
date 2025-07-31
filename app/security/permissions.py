"""
Security module for managing user roles and permissions.

Provides utilities for defining permissions, mapping roles to allowed actions,
and a FastAPI dependency for enforcing permission checks on requests.
"""

from dataclasses import dataclass
from typing import Iterable

from fastapi import HTTPException, Request, status

from app.enums import PermissionEntity as Entity
from app.enums import PermissionVerb as Verb
from app.enums import UserRole


@dataclass(frozen=True)
class Permission:
    """
    Represents a specific permission, defined by an action (verb) on an entity.

    Attributes:
        verb (PermissionVerb): The action permitted (e.g., VIEW, CREATE).
        entity (PermissionEntity): The target entity of the action
                (e.g., COMPANY).
    """

    verb: Verb
    entity: Entity

    def __str__(self) -> str:
        """
        Render the permission as a string in the format 'VERB.ENTITY'.

        Returns:
            str: The string representation of the permission.
        """
        return f'{self.verb}.{self.entity}'


# Note:
#
# Current implementation limits the ability of 'dynamic' user permissions.
# Once you are assigned to a role, only way to get expanded permissions on the
# Platform for a specific user is to allow the whole role more permissions
# This may be the inteded behavior, but I am not sure.

ROLE_PERMISSIONS = {
    UserRole.ADMIN: {
        # Global data access
        (Verb.VIEW, Entity.ALL_DATA),
        # User management
        (Verb.VIEW, Entity.ALL_USERS),
        (Verb.CREATE, Entity.USER),
        (Verb.UPDATE, Entity.USER),
        (Verb.DELETE, Entity.ALL_USERS),
        # Role management
        (Verb.VIEW, Entity.ALL_ROLES),
        (Verb.ASSIGN, Entity.ROLE),
        # Company
        (Verb.VIEW, Entity.COMPANY),
        (Verb.CREATE, Entity.COMPANY),
        (Verb.UPDATE, Entity.COMPANY),
        (Verb.DELETE, Entity.COMPANY),
        # Company address
        (Verb.VIEW, Entity.COMPANY_ADDRESS),
        (Verb.CREATE, Entity.COMPANY_ADDRESS),
        (Verb.UPDATE, Entity.COMPANY_ADDRESS),
        (Verb.DELETE, Entity.COMPANY_ADDRESS),
    },
    UserRole.BUYER: {
        (Verb.VIEW, Entity.COMPANY),
        (Verb.VIEW, Entity.COMPANY_ADDRESS),
    },
    UserRole.SELLER: {
        (Verb.VIEW, Entity.COMPANY),
        (Verb.VIEW, Entity.COMPANY_ADDRESS),
    },
    UserRole.ISSUER: {
        (Verb.VIEW, Entity.COMPANY),
        (Verb.UPDATE, Entity.COMPANY),
        (Verb.VIEW, Entity.COMPANY_ADDRESS),
        (Verb.CREATE, Entity.COMPANY_ADDRESS),
        (Verb.UPDATE, Entity.COMPANY_ADDRESS),
        (Verb.DELETE, Entity.COMPANY_ADDRESS),
    },
}


# TODO: Move this dependency into a dependency folder/file
def has_permission(required: Iterable[Permission]):
    """
    Create a FastAPI dependency that enforces at least one required permission.

    This dependency inspects the incoming request's `state.user` attribute,
    retrieves the user's role, and checks whether the role's permission set
    includes any of the permissions specified in `required`. If the user is
    not authenticated or lacks the necessary permission, an HTTPException is
    raised.

    Args:
        required (Iterable[Permission]): An iterable of Permission instances
            to check.

    Returns:
        Callable: A dependency function to be used with FastAPI's Depends.

    Raises:
        HTTPException:
            - 401 Unauthorized if no user is found on request.state.user.
            - 403 Forbidden if the user lacks all of the required permissions.
    """

    def permission_dependency(request: Request) -> None:
        """
        FastAPI dependency that performs the permission check on the request.

        Args:
            request (Request): The incoming FastAPI request, expected to have
                a `state.user` attribute with `role: UserRole`.

        Raises:
            HTTPException:
                - 401 Unauthorized if `request.state.user` is missing.
                - 403 Forbidden if the user's role does not grant any of the
                  required permissions.
        """
        # TODO: Pull in the actual user data into this
        user = getattr(request.state, 'user', None)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail='Unauthorized'
            )

        role: UserRole = user.role
        allowed = ROLE_PERMISSIONS.get(role, set())
        if not any(p in allowed for p in required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Insufficient permissions',
            )

    return permission_dependency
