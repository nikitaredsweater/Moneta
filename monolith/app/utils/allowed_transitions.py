"""
Allowed Status Transitions Module.

This module centralizes all status transition rules for transitionable entities
in the system. Transitions are defined per user role and per entity type.

Usage:
    from app.utils.allowed_transitions import get_allowed_transitions

    # Get allowed transitions for a listing by an ADMIN
    allowed = get_allowed_transitions(
        entity=TransitionableEntity.LISTING,
        role=UserRole.ADMIN,
    )
    # Returns: {ListingStatus.OPEN: [ListingStatus.SUSPENDED, ListingStatus.CLOSED], ...}

    # Check if a specific transition is allowed
    if ListingStatus.SUSPENDED in allowed.get(ListingStatus.OPEN, []):
        # Transition is allowed
        pass
"""

from enum import Enum
from typing import Dict, List, Optional, Type

from app.enums import AskStatus, BidStatus, ListingStatus
from app.enums.transitionable_entity import TransitionableEntity
from moneta_auth import UserRole


# Type alias for transition mappings
# Maps: current_status -> list of allowed target statuses
TransitionMap = Dict[Enum, List[Enum]]

# Type alias for role-based transition mappings
# Maps: role -> transition_map
RoleTransitionMap = Dict[UserRole, TransitionMap]

# Type alias for entity-based transition mappings
# Maps: entity -> role_transition_map
EntityTransitionMap = Dict[TransitionableEntity, RoleTransitionMap]


# =============================================================================
#                               LISTING TRANSITIONS
# =============================================================================

LISTING_TRANSITIONS: RoleTransitionMap = {
    UserRole.ADMIN: {
        ListingStatus.OPEN: [ListingStatus.SUSPENDED, ListingStatus.CLOSED],
        ListingStatus.WITHDRAWN: [
            ListingStatus.SUSPENDED,
            ListingStatus.CLOSED,
            ListingStatus.OPEN,
        ],
        ListingStatus.SUSPENDED: [
            ListingStatus.OPEN,
            ListingStatus.CLOSED,
        ],
        ListingStatus.CLOSED: [
            ListingStatus.OPEN,
        ],
    },
    UserRole.BUYER: {
        # Buyers cannot transition listings
    },
    UserRole.SELLER: {
        # Sellers (company users) can only withdraw their own open listings
        ListingStatus.OPEN: [ListingStatus.WITHDRAWN],
    },
    UserRole.ISSUER: {
        # Issuers can also withdraw their own open listings (same as sellers)
        ListingStatus.OPEN: [ListingStatus.WITHDRAWN],
    },
}


# =============================================================================
#                               BID TRANSITIONS
# =============================================================================

BID_TRANSITIONS: RoleTransitionMap = {
    UserRole.ADMIN: {
        # Admin can suspend pending or withdrawn bids
        BidStatus.PENDING: [BidStatus.SUSPENDED],
        BidStatus.WITHDRAWN: [BidStatus.SUSPENDED],
    },
    UserRole.BUYER: {
        # Buyers (bidder company) can withdraw their pending bids
        BidStatus.PENDING: [BidStatus.WITHDRAWN],
    },
    UserRole.SELLER: {
        # Sellers cannot transition bids directly via the transition endpoint
        # (they use accept/reject endpoints instead)
    },
    UserRole.ISSUER: {
        # Issuers cannot transition bids
    },
}


# =============================================================================
#                                   ASK TRANSITIONS
# =============================================================================

ASK_TRANSITIONS: RoleTransitionMap = {
    UserRole.ADMIN: {
        # Admin can suspend active or withdrawn asks, and reactivate suspended asks
        AskStatus.ACTIVE: [AskStatus.SUSPENDED],
        AskStatus.WITHDRAWN: [AskStatus.SUSPENDED],
        AskStatus.SUSPENDED: [AskStatus.ACTIVE],
    },
    UserRole.BUYER: {
        # Buyers cannot transition asks
    },
    UserRole.SELLER: {
        # Sellers (asker company) can withdraw their active asks
        AskStatus.ACTIVE: [AskStatus.WITHDRAWN],
    },
    UserRole.ISSUER: {
        # Issuers can also withdraw their active asks (same as sellers)
        AskStatus.ACTIVE: [AskStatus.WITHDRAWN],
    },
}


# =============================================================================
#                           MASTER TRANSITIONS MAP
# =============================================================================

ALL_TRANSITIONS: EntityTransitionMap = {
    TransitionableEntity.LISTING: LISTING_TRANSITIONS,
    TransitionableEntity.BID: BID_TRANSITIONS,
    TransitionableEntity.ASK: ASK_TRANSITIONS,
}


# =============================================================================
#                           STATUS ENUM MAPPING
# =============================================================================

ENTITY_STATUS_ENUM: Dict[TransitionableEntity, Type[Enum]] = {
    TransitionableEntity.LISTING: ListingStatus,
    TransitionableEntity.BID: BidStatus,
    TransitionableEntity.ASK: AskStatus,
}


# =============================================================================
#                                 PUBLIC API
# =============================================================================


def get_allowed_transitions(
    entity: TransitionableEntity,
    role: UserRole,
) -> TransitionMap:
    """
    Get the allowed status transitions for a given entity type and user role.

    Args:
        entity: The type of entity (LISTING, BID, ASK).
        role: The user role requesting the transitions.

    Returns:
        A dictionary mapping current status to list of allowed target statuses.
        Returns an empty dict if no transitions are defined for the role.

    Example:
        >>> transitions = get_allowed_transitions(
        ...     entity=TransitionableEntity.LISTING,
        ...     role=UserRole.ADMIN,
        ... )
        >>> transitions[ListingStatus.OPEN]
        [ListingStatus.SUSPENDED, ListingStatus.CLOSED]
    """
    entity_transitions = ALL_TRANSITIONS.get(entity, {})
    return entity_transitions.get(role, {})


def is_transition_allowed(
    entity: TransitionableEntity,
    role: UserRole,
    current_status: Enum,
    target_status: Enum,
) -> bool:
    """
    Check if a specific status transition is allowed for a given entity and role.

    Args:
        entity: The type of entity (LISTING, BID, ASK).
        role: The user role attempting the transition.
        current_status: The current status of the entity.
        target_status: The desired target status.

    Returns:
        True if the transition is allowed, False otherwise.

    Example:
        >>> is_transition_allowed(
        ...     entity=TransitionableEntity.LISTING,
        ...     role=UserRole.ADMIN,
        ...     current_status=ListingStatus.OPEN,
        ...     target_status=ListingStatus.SUSPENDED,
        ... )
        True
    """
    transitions = get_allowed_transitions(entity, role)
    allowed_targets = transitions.get(current_status, [])
    return target_status in allowed_targets


def get_status_enum_for_entity(
    entity: TransitionableEntity,
) -> Optional[Type[Enum]]:
    """
    Get the status enum class associated with a transitionable entity.

    Args:
        entity: The type of entity (LISTING, BID, ASK).

    Returns:
        The Enum class for the entity's status, or None if not found.

    Example:
        >>> get_status_enum_for_entity(TransitionableEntity.LISTING)
        <enum 'ListingStatus'>
    """
    return ENTITY_STATUS_ENUM.get(entity)
