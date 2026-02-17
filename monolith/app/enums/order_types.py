"""
Order types enum, signalling the type of incoming order.
"""

from enum import Enum


class OrderType(str, Enum):
    """
    Order type enum.
    """

    SELL = 'sell'
    BUY = 'buy'
    CANCEL = 'cancel'
    MODIFY = 'modify'
