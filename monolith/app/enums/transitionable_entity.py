"""
Enum for entities that support status transitions.
"""

from enum import Enum


class TransitionableEntity(str, Enum):
    """
    Entities in the system that have status fields supporting transitions.

    These entities have defined state machines with allowed transitions
    that vary based on user role.
    """

    LISTING = 'LISTING'
    BID = 'BID'
    ASK = 'ASK'
