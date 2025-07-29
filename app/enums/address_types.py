"""
module for enums for addresses of companies
"""

from enum import Enum


class AddressType(Enum):
    REGISTERED = 'REGISTERED'
    BILLING = 'BILLING'
    OFFICE = 'OFFICE'
    SHIPPING = 'SHIPPING'
    OTHER = 'OTHER'
