"""
module for enums for instrument trading status - not the same as successful
maturity status
"""

from enum import Enum


class InstrumentStatus(str, Enum):
    """
    Status of the receivable being allowed to trade on the platform.

    Only shows the amdinistrative status and does not have anything to do
    with the trade life-cycle or maturity payouts.
    """

    DRAFT = 'DRAFT'  # issuer/owner still editing
    PENDING_APPROVAL = 'PENDING_APPROVAL'  # sent for review
    ACTIVE = 'ACTIVE'  # eligible for listing/trade
    MATURED = 'MATURED'  # no longer maintained/listable
    REJECTED = 'REJECTED'  # failed review
    SUSPENDED = 'SUSPENDED'  # failed review


class MaturityStatus(str, Enum):
    """
    Maturity payouts statuses.
    """

    NOT_DUE = 'NOT_DUE'  # future maturity date
    DUE = 'DUE'  # payment date reached
    IN_GRACE = 'IN_GRACE'  # within contractual grace period
    PARTIALLY_PAID = (
        'PARTIALLY_PAID'  # paid not in full (we do not track how much was paid)
    )
    PAID = 'PAID'  # fully settled as promised
    LATE = 'LATE'  # beyond grace, not default yet (policy-defined)
    DEFAULTED = 'DEFAULTED'  # event of default triggered
    DISPUTED = 'DISPUTED'  # payment/discrepancy under dispute
