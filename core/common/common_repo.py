from typing import List, Optional, TypeVar

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.common.common_schema import DependencyCheckSchema

T = TypeVar("T")


class CommonRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def add(
        self,
        orm_instance: T,
        where_stmt=None,
    ) -> T:
        if not isinstance(where_stmt, tuple) and where_stmt is not None:
            where_stmt = (where_stmt,)

        if where_stmt is not None:
            existing_instance: T = (
                await self.session.execute(
                    select(type(orm_instance)).where(*where_stmt)
                )
            ).scalar()

            if existing_instance:
                return existing_instance

        self.session.add(orm_instance)
        await self.session.flush()
        return orm_instance

    async def add_all(
        self,
        orm_instances: list[T],
    ) -> list[T]:
        self.session.add_all(orm_instances)
        await self.session.flush()
        return orm_instances

    async def update(self, orm_instance: T) -> T:
        await self.session.merge(orm_instance)
        await self.session.flush()
        return orm_instance

    async def update_stmt(
        self,
        table: type[T],
        where_stmt,
        values: dict,
    ):
        if not isinstance(where_stmt, tuple):
            where_stmt = (where_stmt,)

        await self.session.execute(
            update(table)
            .where(*where_stmt)
            .values(
                **values,
            )
        )
        await self.session.flush()

    async def get_one(
        self,
        from_table: type[T],
        where_stmt,
    ) -> Optional[T]:
        if not isinstance(where_stmt, tuple):
            where_stmt = (where_stmt,)

        return (
            await self.session.execute(select(from_table).where(*where_stmt))
        ).scalar()

    async def get_all_scalars(
        self,
        from_table: type[T],
        where_stmt=None,
    ) -> list[T]:
        if not isinstance(where_stmt, tuple) and where_stmt is not None:
            where_stmt = (where_stmt,)

        stmt = select(from_table)

        if where_stmt:
            stmt = stmt.where(*where_stmt)

        return (await self.session.execute(stmt)).scalars().all()

    async def get_all_mappings(self, select_tuple, where_stmt=None):
        if not isinstance(where_stmt, tuple) and where_stmt is not None:
            where_stmt = (where_stmt,)

        if not isinstance(select_tuple, tuple):
            select_tuple = (select_tuple,)

        stmt = select(*select_tuple)

        if where_stmt:
            stmt = stmt.where(*where_stmt)

        return (await self.session.execute(stmt)).mappings().all()

    async def delete(self, from_table: type[T], where_stmt) -> int:
        if not isinstance(where_stmt, tuple):
            where_stmt = (where_stmt,)

        result = await self.session.execute(delete(from_table).where(*where_stmt))
        await self.session.flush()
        return result.rowcount

    async def check_dependencies(
        self,
        dependencies: List[DependencyCheckSchema],
    ):
        """
        True if ok
        """
        for dependency in dependencies:
            existing_instance: T = await self.session.get(
                dependency.table,
                dependency.id,
            )

            if not existing_instance:
                return dependency.table

        return True
