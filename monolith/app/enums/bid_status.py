"""
Enum for bid statuses.
"""

from enum import Enum


class BidStatus(str, Enum):
    """
    Status of a bid on a listing.

    PENDING - Bid is active and awaiting decision
    WITHDRAWN - Bid was voluntarily withdrawn by the bidder
    SUSPENDED - Bid was suspended by admin/platform
    SELECTED - Bid was selected/accepted by the seller
    NOT_SELECTED - Bid was not selected (either rejected or another bid was selected)
    """

    PENDING = 'PENDING'
    WITHDRAWN = 'WITHDRAWN'
    SUSPENDED = 'SUSPENDED'
    SELECTED = 'SELECTED'
    NOT_SELECTED = 'NOT_SELECTED'
