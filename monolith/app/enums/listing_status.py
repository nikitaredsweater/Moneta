"""
Enum for listing statuses.
"""

from enum import Enum


class ListingStatus(str, Enum):
    """
    Status of an instrument listing on the trading platform.

    OPEN - Listing is active and available for trading
    WITHDRAWN - Listing was voluntarily withdrawn by the seller
    SUSPENDED - Listing was suspended by admin/platform
    """

    OPEN = 'OPEN'
    WITHDRAWN = 'WITHDRAWN'
    SUSPENDED = 'SUSPENDED'
