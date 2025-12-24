"""
user roles

DEPRECATED: This module is deprecated. Use moneta_auth package instead.
- from moneta_auth import UserRole
"""

from enum import Enum


class UserRole(str, Enum):
    ADMIN = 'ADMIN'
    BUYER = 'BUYER'
    SELLER = 'SELLER'
    ISSUER = 'ISSUER'
