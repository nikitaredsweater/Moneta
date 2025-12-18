"""
Base PG repository
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import (
    Any,
    Callable,
    ClassVar,
    Generic,
    Iterable,
    List,
    Optional,
    Type,
    TypeVar,
    cast,
)

from app.models.base import BaseEntity
from app.schemas.base import BaseDTO, MonetaID
from sqlalchemy import desc, func, inspect, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, sessionmaker

T = TypeVar("T", bound=BaseDTO)

# FIXME: Copmly with the code standards!


class BasePGRepository(Generic[T]):
    """Base Posgtes Repository"""

    class Meta:  # pylint: disable=too-few-public-methods
        response_model = BaseDTO
        orm_model = BaseEntity
        exclusion_fields: Optional[set]

    _instances: ClassVar[dict[sessionmaker, BasePGRepository]] = {}

    def __init__(self, session: sessionmaker):
        self.session = session

    @classmethod
    def make_fastapi_dep(cls, session: sessionmaker) -> Callable:
        """Fast API Depends wrapper"""

        def get_instance() -> BasePGRepository:
            cls._instances = dict(cls._instances)

            if session not in cls._instances:
                cls._instances[session] = cls(session)

            return cls._instances[session]

        return get_instance

    @classmethod
    def to_orm_dict(
        cls, model: T, exclude_unset: bool = False
    ) -> dict[str, Any]:
        """Pydantic -> SQLAlchemy mapper"""
        dict_obj = model.dict(
            exclude=(
                cls.Meta.exclusion_fields
                if hasattr(cls.Meta, "exclusion_fields")
                else {}
            ),
            exclude_unset=exclude_unset,
        )
        for key in dict_obj.keys():
            if isinstance(dict_obj[key], datetime):
                # NOTE: Postgresql can store only UTC dates without timezones
                dict_obj[key] = dict_obj[key].replace(tzinfo=None)
            if isinstance(dict_obj[key], dict):
                # JSON fields, apply pydantic json serialization
                try:
                    dict_obj[key] = json.loads(getattr(model, key).json())
                except AttributeError:
                    # NOTE: skip if it's not pydantic
                    pass
            if isinstance(dict_obj[key], list):
                # JSON fields, apply pydantic json serialization
                try:
                    dict_obj[key] = [
                        (
                            str(item)
                            if isinstance(item, UUID)
                            else json.loads(item.json())
                        )
                        for item in getattr(model, key)
                    ]
                except AttributeError:
                    # NOTE: skip if it's not pydantic
                    pass
        return dict_obj

    @classmethod
    def to_orm(cls, model: T, exclude_unset: bool = False) -> BaseEntity:
        """Pydantic -> SQLAlchemy mapper"""
        return cls.Meta.orm_model(
            **cls.to_orm_dict(model, exclude_unset=exclude_unset)
        )

    @classmethod
    def from_orm(cls, orm_model: BaseEntity) -> T:
        """SQLAlchemy -> Pydantic mapper"""
        return cls.Meta.response_model.from_orm(orm_model)

    @staticmethod
    def from_orm_with_includes(
        orm_model: BaseEntity,
        model_cls: Type[T],
        includes: Optional[Iterable[str]] = None,
    ) -> T:
        """
        Safely convert ORM entity to Pydantic model, handling unloaded relationships.

        This method only includes relationships that were explicitly loaded (via includes).
        Unloaded relationships will use their default values (typically None).

        Args:
            orm_model: The SQLAlchemy ORM model instance
            model_cls: The Pydantic model class to convert to
            includes: List of relationship names that were eagerly loaded

        Returns:
            Pydantic model instance with only loaded relationships populated
        """
        includes_set = set(includes) if includes else set()
        insp = inspect(orm_model)
        mapper = insp.mapper

        # Get all column attribute names (non-relationship fields)
        column_attrs = {c.key for c in mapper.columns}

        # Get all relationship attribute names
        relationship_attrs = {r.key for r in mapper.relationships}

        # Build dict with column values
        data = {}
        for attr in column_attrs:
            data[attr] = getattr(orm_model, attr)

        # Only include relationships that were explicitly loaded
        for attr in relationship_attrs:
            if attr in includes_set:
                data[attr] = getattr(orm_model, attr)
            # Unloaded relationships will use Pydantic's default value (None)

        return model_cls(**data)

    async def create(self, model: T) -> T:
        orm_model = self.to_orm(model)
        session: AsyncSession
        async with self.session() as session:
            async with session.begin():
                session.add(orm_model)
                await session.flush()
                await session.refresh(orm_model)
                return self.from_orm(orm_model)

    @staticmethod
    def normalize_column(column: Any) -> Any:
        """Normalize column for case-insensitive search without special characters"""
        return func.lower(func.regexp_replace(column, r"[^a-zA-Z0-9]", "", "g"))

    async def create_many(self, models: List[T]) -> List[T]:
        """Create many entities at once"""
        orm_models = [self.to_orm(model) for model in models]
        async with self.session() as session:
            async with session.begin():
                try:
                    session.add_all(orm_models)
                    await session.flush()  # Flush to assign any server-generated values to the models

                    # Refreshing each model to ensure all data is up-to-date
                    for orm_model in orm_models:
                        await session.refresh(orm_model)

                    return [
                        self.from_orm(orm_model) for orm_model in orm_models
                    ]
                except SQLAlchemyError as e:
                    await session.rollback()
                    raise e

    async def get_all_by_ids(self, ids: list[MonetaID]) -> list[T]:
        return await self.get_all([self.Meta.orm_model.id.in_(ids)])

    async def get_all(
        self,
        where_list: Optional[list] = None,
        order_list: Optional[list] = None,
        custom_model: Optional[Type[T]] = None,
        deleted: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        includes: Optional[Iterable[str]] = None,
    ) -> list[T]:
        """
        Gets all rows according to where statements

        Args:
          deleted: if True will return deleted records as well
          where_list: list of sqlalchemy where statements
            e.g [Model.id == id, Model.created_by == user_id]
          order_list: list of order statements
          custom_model: Custom pydantic class to map SA model

        Returns:
          list of rows according to filter
        """
        session: AsyncSession
        async with self.session() as session:
            async with session.begin():
                orm_model = self.Meta.orm_model
                query = select(orm_model)

                if not deleted:
                    query = query.where(
                        orm_model.deleted_at == None
                    )  # noqa: E711

                if where_list:
                    for where_clause in where_list:
                        query = query.where(where_clause)

                if offset is not None:
                    query = query.offset(offset)
                if limit is not None:
                    query = query.limit(limit)

                if order_list:
                    for order in order_list:
                        query = query.order_by(order)

                if offset is not None:
                    query = query.offset(offset)
                if limit is not None:
                    query = query.limit(limit)

                if includes:
                    for name in includes:
                        # only apply if the relationship exists
                        if hasattr(orm_model, name):
                            query = query.options(
                                selectinload(getattr(orm_model, name))
                            )

                result = await session.execute(query)
                # Use safe conversion when includes are specified to avoid
                # lazy loading issues with unloaded relationships
                if custom_model and includes:
                    return [
                        self.from_orm_with_includes(
                            entity, custom_model, includes
                        )
                        for entity in result.scalars().unique()
                    ]
                if custom_model:
                    return [
                        custom_model.from_orm(entity)
                        for entity in result.scalars().unique()
                    ]
                return [
                    self.from_orm(entity) for entity in result.scalars().all()
                ]

    async def count_all(self) -> int:
        session: AsyncSession
        async with self.session() as session:
            async with session.begin():
                orm_model = self.Meta.orm_model
                query = select(func.count(orm_model.id))
                return (await session.execute(query)).scalars().first() or 0

    async def get_one(
        self,
        where_list: Optional[list] = None,
        order_list: Optional[list] = None,
    ) -> Optional[T]:
        """Gets one record"""
        session: AsyncSession
        async with self.session() as session:
            async with session.begin():
                orm_model = self.Meta.orm_model
                query = select(orm_model)

                # pylint: disable=singleton-comparison
                query = query.where(orm_model.deleted_at == None)  # noqa: E711

                if where_list:
                    for where_clause in where_list:
                        query = query.where(where_clause)

                if not order_list:
                    order_list = [desc(orm_model.created_at)]

                for order in order_list:
                    query = query.order_by(order)

                query = query.limit(1)

                result = await session.execute(query)

                for entity in result.scalars().unique():
                    return self.from_orm(entity)
                return None

    async def get_by_id(
        self,
        pk: MonetaID,
        deleted: bool = False,
        custom_model: Optional[Type[T]] = None,
        includes: Optional[Iterable[str]] = None,
    ) -> Optional[T]:
        """Gets record by id"""
        session: AsyncSession
        async with self.session() as session:
            async with session.begin():
                orm_model = self.Meta.orm_model
                query = select(orm_model).where(orm_model.id == pk)

                if not deleted:
                    query = query.where(
                        orm_model.deleted_at == None
                    )  # noqa: E711

                if includes:
                    for name in includes:
                        if hasattr(orm_model, name):
                            query = query.options(
                                selectinload(getattr(orm_model, name))
                            )

                result = await session.execute(query)
                entity = result.scalars().first()
                if not entity:
                    return None

                if custom_model is not None:
                    model_cls: Type[T] = custom_model
                else:
                    model_cls = cast(Type[T], self.Meta.response_model)

                # Use safe conversion when includes are specified to avoid
                # lazy loading issues with unloaded relationships
                if includes:
                    return self.from_orm_with_includes(
                        entity, model_cls, includes
                    )

                return model_cls.from_orm(entity)

    async def get_by_ids(
        self, pk_list: list[MonetaID], deleted: bool = False
    ) -> list[T]:
        """Gets records by id list"""
        return await self.get_all(
            [self.Meta.orm_model.id.in_(pk_list)], deleted=deleted
        )

    async def _update_by_id(
        self, pk: MonetaID, update_map: dict
    ) -> Optional[T]:
        """Updates entity based on mapping"""
        session: AsyncSession
        async with self.session() as session:
            async with session.begin():
                orm_model = self.Meta.orm_model
                stmt = (
                    update(orm_model)
                    .values(update_map)
                    .where(orm_model.id == pk)
                )
                await session.execute(stmt)

        return await self.get_by_id(pk, deleted=True)

    async def update_by_id(self, pk: MonetaID, model: T) -> Optional[T]:
        """Updates record by id"""
        update_map = self.to_orm_dict(model, exclude_unset=True)
        return await self._update_by_id(pk, update_map)

    async def update_by_ids(self, pk_list: list[MonetaID], model: T) -> list[T]:
        """Updates records by id list"""
        update_map = self.to_orm_dict(model, exclude_unset=True)
        session: AsyncSession
        async with self.session() as session:
            async with session.begin():
                orm_model = self.Meta.orm_model
                stmt = (
                    update(orm_model)
                    .values(update_map)
                    .where(self.Meta.orm_model.id.in_(pk_list))
                )
                await session.execute(stmt)

        return await self.get_all_by_ids(pk_list)

    async def update_many(
        self, model: T, where_list: Optional[list] = None
    ) -> None:
        """Updates many records"""
        update_map = self.to_orm_dict(model, exclude_unset=True)
        session: AsyncSession
        async with self.session() as session:
            async with session.begin():
                orm_model = self.Meta.orm_model
                stmt = update(orm_model).values(update_map)

                if where_list:
                    for where_clause in where_list:
                        stmt = stmt.where(where_clause)

                await session.execute(stmt)

    async def delete_by_id(self, pk: MonetaID) -> Optional[T]:
        """Deletes record by id"""
        return await self._update_by_id(pk, {"deleted_at": datetime.utcnow()})

    async def delete_many(self, where_list: Optional[list] = None) -> None:
        """Deletes many records"""
        session: AsyncSession
        async with self.session() as session:
            async with session.begin():
                orm_model = self.Meta.orm_model
                stmt = update(orm_model).values(
                    {"deleted_at": datetime.utcnow()}
                )

                if where_list:
                    for where_clause in where_list:
                        stmt = stmt.where(where_clause)

                await session.execute(stmt)

    async def delete_by_ids(self, pk_list: list[MonetaID]) -> None:
        """Deletes records by id list"""
        await self.delete_many([self.Meta.orm_model.id.in_(pk_list)])


class ProjectChildORM(BaseEntity):
    project_id: MonetaID


class ProjectChildRepo(BasePGRepository[T], Generic[T]):

    class Meta:  # pylint: disable=too-few-public-methods
        response_model = BaseDTO
        orm_model = ProjectChildORM
        exclusion_fields: Optional[set]

    async def get_all_by_project_id(self, project_id: MonetaID) -> list[T]:
        # TODO: move this to mixin
        return await self.get_all(
            [self.Meta.orm_model.project_id == project_id]
        )
