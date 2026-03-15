from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.document import FolderOrm


class FolderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, folder_id: int) -> Optional[FolderOrm]:
        return (
            await self.session.execute(
                select(FolderOrm).where(FolderOrm.id == folder_id)
            )
        ).scalar()

    async def get_children(self, parent_id: Optional[int]) -> list[FolderOrm]:
        return (
            await self.session.execute(
                select(FolderOrm).where(FolderOrm.parent_id == parent_id)
            )
        ).scalars().all()

    async def get_descendants(self, path_prefix: str) -> list[FolderOrm]:
        return (
            await self.session.execute(
                select(FolderOrm).where(FolderOrm.path.like(f"{path_prefix}%"))
            )
        ).scalars().all()
