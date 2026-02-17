"""
Enum for ask statuses and execution modes.
"""

from enum import Enum


class AskStatus(str, Enum):
    """
    Status of an ask on a listing.

    ACTIVE - Ask is active and accepting bids
    WITHDRAWN - Ask was voluntarily withdrawn by the asker
    SUSPENDED - Ask was suspended by admin/platform
    """

    ACTIVE = 'ACTIVE'
    WITHDRAWN = 'WITHDRAWN'
    SUSPENDED = 'SUSPENDED'


class ExecutionMode(str, Enum):
    """
    Execution mode for an ask.

    AUTO - Bids matching the ask price are automatically accepted
    MANUAL - Bids require manual review and acceptance by the seller
    """

    AUTO = 'AUTO'
    MANUAL = 'MANUAL'
