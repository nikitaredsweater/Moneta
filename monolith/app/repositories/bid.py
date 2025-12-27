"""
This module contains the functions to interact with the bids table.

All of the interaction with the bids table should be done through
this module.
"""

from typing import Annotated, List

from app import models, schemas
from app.enums import BidStatus
from app.repositories.base import BasePGRepository
from app.schemas.base import MonetaID
from app.utils.session import async_session
from fastapi import Depends


class BidRepository(BasePGRepository[schemas.Bid]):
    class Meta:
        response_model = schemas.Bid
        orm_model = models.Bid
        exclusion_fields = None
        eager_relations = [models.Bid.listing]

    async def get_by_listing_id(
        self, listing_id: MonetaID
    ) -> List[schemas.Bid]:
        """Get all bids for a listing."""
        return await self.get_all(
            [self.Meta.orm_model.listing_id == listing_id]
        )

    async def get_by_bidder_company_id(
        self, bidder_company_id: MonetaID
    ) -> List[schemas.Bid]:
        """Get all bids by a bidder company."""
        return await self.get_all(
            [self.Meta.orm_model.bidder_company_id == bidder_company_id]
        )

    async def get_pending_bids_for_listing(
        self, listing_id: MonetaID
    ) -> List[schemas.Bid]:
        """Get all PENDING bids for a listing."""
        return await self.get_all(
            [
                self.Meta.orm_model.listing_id == listing_id,
                self.Meta.orm_model.status == BidStatus.PENDING,
            ]
        )

    async def get_pending_bids_for_listing_except(
        self, listing_id: MonetaID, exclude_bid_id: MonetaID
    ) -> List[schemas.Bid]:
        """Get all PENDING bids for a listing except the specified bid."""
        return await self.get_all(
            [
                self.Meta.orm_model.listing_id == listing_id,
                self.Meta.orm_model.status == BidStatus.PENDING,
                self.Meta.orm_model.id != exclude_bid_id,
            ]
        )

    async def update_status(
        self, bid_id: MonetaID, new_status: BidStatus
    ) -> schemas.Bid | None:
        """Update the status of a bid."""
        return await self.update_by_id(
            bid_id,
            schemas.BidStatusUpdate(status=new_status),
        )


Bid = Annotated[
    BidRepository,
    Depends(BidRepository.make_fastapi_dep(async_session)),
]
