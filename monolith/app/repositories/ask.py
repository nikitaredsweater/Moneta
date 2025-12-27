"""
This module contains the functions to interact with the asks table.

All of the interaction with the asks table should be done through
this module.
"""

from typing import Annotated, List

from app import models, schemas
from app.enums import AskStatus
from app.repositories.base import BasePGRepository
from app.schemas.base import MonetaID
from app.utils.session import async_session
from fastapi import Depends


class AskRepository(BasePGRepository[schemas.Ask]):
    class Meta:
        response_model = schemas.Ask
        orm_model = models.Ask
        exclusion_fields = None
        eager_relations = [models.Ask.listing]

    async def get_by_listing_id(
        self, listing_id: MonetaID
    ) -> List[schemas.Ask]:
        """Get all asks for a listing."""
        return await self.get_all(
            [self.Meta.orm_model.listing_id == listing_id]
        )

    async def get_active_asks_for_listing(
        self, listing_id: MonetaID
    ) -> List[schemas.Ask]:
        """Get all ACTIVE asks for a listing."""
        return await self.get_all(
            [
                self.Meta.orm_model.listing_id == listing_id,
                self.Meta.orm_model.status == AskStatus.ACTIVE,
            ]
        )

    async def get_by_asker_company_id(
        self, asker_company_id: MonetaID
    ) -> List[schemas.Ask]:
        """Get all asks by an asker company."""
        return await self.get_all(
            [self.Meta.orm_model.asker_company_id == asker_company_id]
        )

    async def update_status(
        self, ask_id: MonetaID, new_status: AskStatus
    ) -> schemas.Ask | None:
        """Update the status of an ask."""
        return await self.update_by_id(
            ask_id,
            schemas.AskStatusUpdate(status=new_status),
        )


Ask = Annotated[
    AskRepository,
    Depends(AskRepository.make_fastapi_dep(async_session)),
]
