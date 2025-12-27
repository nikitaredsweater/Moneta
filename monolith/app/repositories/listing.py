"""
This module contains the functions to interact with the listings table.

All of the interaction with the listings table should be done through
this module.
"""

from typing import Annotated

from app import models, schemas
from app.enums import ListingStatus
from app.repositories.base import BasePGRepository
from app.schemas.base import MonetaID
from app.utils.session import async_session
from fastapi import Depends


class ListingRepository(BasePGRepository[schemas.Listing]):
    class Meta:
        response_model = schemas.Listing
        orm_model = models.Listing
        exclusion_fields = None
        eager_relations = [models.Listing.instrument]

    async def get_by_instrument_id(
        self, instrument_id: MonetaID
    ) -> list[schemas.Listing]:
        """Get all listings for an instrument."""
        return await self.get_all(
            [self.Meta.orm_model.instrument_id == instrument_id]
        )

    async def get_by_seller_company_id(
        self, seller_company_id: MonetaID
    ) -> list[schemas.Listing]:
        """Get all listings by a seller company."""
        return await self.get_all(
            [self.Meta.orm_model.seller_company_id == seller_company_id]
        )

    async def get_open_listing_for_instrument(
        self, instrument_id: MonetaID
    ) -> schemas.Listing | None:
        """
        Get the OPEN listing for an instrument if one exists.
        Only one OPEN listing can exist per instrument.
        """
        results = await self.get_all(
            [
                self.Meta.orm_model.instrument_id == instrument_id,
                self.Meta.orm_model.status == ListingStatus.OPEN,
            ]
        )
        return results[0] if results else None

    async def has_open_listing(self, instrument_id: MonetaID) -> bool:
        """Check if an instrument has an OPEN listing."""
        existing = await self.get_open_listing_for_instrument(instrument_id)
        return existing is not None


Listing = Annotated[
    ListingRepository,
    Depends(ListingRepository.make_fastapi_dep(async_session)),
]
