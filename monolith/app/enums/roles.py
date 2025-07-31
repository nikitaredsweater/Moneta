"""
user roles
"""

from enum import Enum


class UserRole(str, Enum):
    ADMIN = 'ADMIN'
    BUYER = 'BUYER'
    SELLER = 'SELLER'
    ISSUER = 'ISSUER'
