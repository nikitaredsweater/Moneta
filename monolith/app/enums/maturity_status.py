"""
module for enums for instrument maturity status
"""
from enum import Enum


class MaturityStatus(str, Enum):
    NOT_TRADING = 'NOT_TRADING'  # Before the instrument became publicly tardable
    PENDING = "PENDING"          # Before maturity
    SETTLED = "SETTLED"          # Paid in full
    DEFAULTED = "DEFAULTED"      # Failed to settle