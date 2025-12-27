"""
Enums that are a part of the ?include optional field for many of the entities
in the system.
"""

from enum import Enum


class CompanyInclude(str, Enum):
    """
    Entities that can be additionally searched for when looking up a company
    object.
    """

    ADDRESSES = "addresses"
    USERS = "users"
    INSTRUMENTS = "instruments"


class InstrumentInclude(str, Enum):
    """
    Entities that can be additionally searched for when looking up an instrument
    object.
    """

    DOCUMENTS = "documents"


class ListingInclude(str, Enum):
    """
    Entities that can be additionally searched for when looking up a listing
    object.
    """

    INSTRUMENT = "instrument"


class BidInclude(str, Enum):
    """
    Entities that can be additionally searched for when looking up a bid
    object.
    """

    LISTING = "listing"
