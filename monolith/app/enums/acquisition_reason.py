"""
Enum for instrument acquisition reasons.
"""

from enum import Enum


class AcquisitionReason(str, Enum):
    """
    Reason for acquiring ownership of an instrument.

    ISSUANCE - Initial ownership when instrument is created
    TRADE - Ownership acquired through a trade/purchase
    ASSIGNMENT - Ownership transferred via legal assignment
    """

    ISSUANCE = 'ISSUANCE'
    TRADE = 'TRADE'
    ASSIGNMENT = 'ASSIGNMENT'
