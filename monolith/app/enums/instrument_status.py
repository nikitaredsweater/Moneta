"""
module for enums for instrument trading status - not the same as successful
maturity status
"""
from enum import Enum

class InstrumentStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    ACTIVE = "ACTIVE"
    MATURED = "MATURED"