"""
security module related to the work with the roles and permissions
"""

from dataclasses import dataclass
from typing import Iterable

from app.enums import PermissionEntity as Entity
from app.enums import PermissionVerb as Verb
from app.enums import UserRole


@dataclass(frozen=True)
class Permission:
    verb: Verb
    entity: Entity

    def __str__(self) -> str:
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


def has_permission(role: UserRole, required: Iterable[Permission]) -> bool:
    """
    Check whether the given user role has at least one of the
    required permissions.

    This function compares the provided list of permissions against the set of
    permissions allowed for the specified role.
    It returns True if any one of the required permissions is present in the
    role's permission set.

    Args:
        role (UserRole): The role of the user being checked.
        required (Iterable[Permission]): A list or set of permissions to check.

    Returns:
        bool: True if the role has at least one of the required permissions,
            False otherwise.
    """
    allowed = ROLE_PERMISSIONS.get(role, set())
    return any(p in allowed for p in required)
