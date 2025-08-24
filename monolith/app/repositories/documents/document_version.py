"""
This module contains the functions to interact with the document_versions table.

All of the interaction with the document_versions table should be done through
this module.
"""

from typing import Annotated
from datetime import datetime
from uuid import UUID

from app import models, schemas
from fastapi import Depends

from sqlalchemy import bindparam, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.repositories.base import BasePGRepository
from app.utils.session import async_session

class DocumentVersionRepository(BasePGRepository[schemas.DocumentVersion]):
    class Meta:
        response_model = schemas.DocumentVersion  # This should be your schema
        orm_model = models.DocumentVersion  # This should be your ORM model
        exclusion_fields = None

    async def create_next_version(
        self,
        *,
        document_id: UUID,
        storage_version_id: str,
        created_by: UUID,
        created_at: datetime,
        max_retries: int = 5,
    ) -> schemas.DocumentVersion:
        """
        Atomically inserts the *next* version for a document using a single
        INSERT ... SELECT with MAX(version_number)+1 and ON CONFLICT DO NOTHING.

        Requires a UNIQUE constraint on (document_id, version_number):
            uq_document_versions_doc_ver

        SQL Executed in the background.
        WITH next AS (
            SELECT COALESCE(MAX(version_number), 0) + 1 AS n
            FROM document_versions
            WHERE document_id = :doc_id
        )
        INSERT INTO document_versions (
            document_id, version_number,
            storage_version_id, created_by, created_at
        )
        SELECT :doc_id, n, :storage_version_id, :created_by, :created_at
        FROM next
        ON CONFLICT (document_id, version_number) DO NOTHING
        RETURNING id, version_number;

        Retries a few times if another writer grabs the same version number.
        """
        table = self.Meta.orm_model.__table__

        # SELECT COALESCE(MAX(version_number), 0) + 1 FOR this document
        next_n = (
            select(func.coalesce(func.max(table.c.version_number), 0) + 1)
            .where(table.c.document_id == bindparam("doc_id"))
            .scalar_subquery()
        )

        # INSERT document_id, next_n, storage_version_id, created_by, created_at
        insert_stmt = (
            pg_insert(table)
            .from_select(
                ["document_id", "version_number", "storage_version_id", "created_by", "created_at"],
                select(
                    bindparam("doc_id"),
                    next_n,
                    bindparam("storage_version_id"),
                    bindparam("created_by"),
                    bindparam("created_at"),
                ),
            )
            # If you also added UNIQUE(document_id, storage_version_id), you can omit the target
            # and just use .on_conflict_do_nothing() to ignore any unique violation.
            .on_conflict_do_nothing(constraint="uq_document_versions_doc_ver")
            .returning(table.c.id)
        )

        params = {
            "doc_id": document_id,
            "storage_version_id": storage_version_id,
            "created_by": created_by,
            # BasePGRepository stores naive UTC; strip tzinfo to be consistent
            "created_at": created_at.replace(tzinfo=None) if created_at.tzinfo else created_at,
        }

        attempt = 0
        async with self.session() as session:
            while True:
                attempt += 1
                async with session.begin():
                    res = await session.execute(insert_stmt, params)
                    row = res.first()
                    if row:
                        version_pk = row[0]
                        obj = await session.get(self.Meta.orm_model, version_pk)
                        return self.from_orm(obj)

                if attempt >= max_retries:
                    raise RuntimeError(
                        "Could not allocate a version number after retries (contention)."
                    )


DocumentVersion = Annotated[
    DocumentVersionRepository,
    Depends(DocumentVersionRepository.make_fastapi_dep(async_session)),
]
