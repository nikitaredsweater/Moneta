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


class TradingStatus(str, Enum):
    """
    Status of a receivable in its trade lifecycle.
    """

    OFF_MARKET = "OFF_MARKET"  # held, not listed
    DRAFT = "DRAFT"  # preparing a listing
    LISTED = "LISTED"  # publicly available for offers
    PAUSED = "PAUSED"  # temporarily hidden by owner
    UNDER_OFFER = "UNDER_OFFER"  # an offer accepted; negotiating/confirming
    RESERVED = "RESERVED"  # exclusivity window for a buyer
    ESCROW = "ESCROW"  # docs/funds in escrow
    SETTLEMENT_PENDING = (
        "SETTLEMENT_PENDING"  # registrar/ops executing transfer
    )
    CANCELLED = "CANCELLED"  # owner withdrew the listing
    EXPIRED = "EXPIRED"  # listing timed out
    SUSPENDED = "SUSPENDED"  # platform/compliance hold
    FAILED_SETTLEMENT = "FAILED_SETTLEMENT"  # unwind
