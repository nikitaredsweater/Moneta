"""
module for enums for user's statuses of their accounts.

DEPRECATED: This module is deprecated. Use moneta_auth package instead.
- from moneta_auth import ActivationStatus
"""

from enum import Enum


class ActivationStatus(str, Enum):
    """
    All possible options for user accounts' activation.
    """

    ACTIVE = 'ACTIVE'  # User is fully active
    INACTIVE = 'INACTIVE'  # User exists but is not currently active
    PENDING = 'PENDING'  # Waiting for email/phone verification
    SUSPENDED = 'SUSPENDED'  # Temporarily disabled by admins
    DISABLED = 'DISABLED'  # Permanently disabled by admins
    DELETED = 'DELETED'  # Soft-deleted (account removed but recoverable)
    BANNED = 'BANNED'  # Permanently banned for violations
    LOCKED = 'LOCKED'  # Usually after failed login attempts
    AWAITING_APPROVAL = 'AWAITING_APPROVAL'  # Requires manual admin review
    REJECTED = 'REJECTED'  # Rejected during onboarding/KYC
    ARCHIVED = 'ARCHIVED'  # Old, unused account archived
    UNVERIFIED = 'UNVERIFIED'  # Registered but email/phone not confirmed
