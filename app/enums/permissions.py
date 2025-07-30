"""
User permissions. Should be configured based on their role
"""

from enum import Enum


class PermissionVerb(str, Enum):
    VIEW = 'VIEW'
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    ASSIGN = 'ASSIGN'


class PermissionEntity(str, Enum):
    USER = 'USER'
    COMPANY = 'COMPANY'
    COMPANY_ADDRESS = 'COMPANY_ADDRESS'
    ROLE = 'ROLE'
    # If not ALL_ ,then assume that the action can be
    # performed on the entity associated with the given user only
    ALL_DATA = 'ALL_DATA'
    ALL_USERS = 'ALL_USERS'
    ALL_ROLES = 'ALL_ROLES'
