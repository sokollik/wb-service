from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.document import DocumentOrm


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, doc_id: int) -> Optional[DocumentOrm]:
        return (
            await self.session.execute(
                select(DocumentOrm).where(DocumentOrm.id == doc_id)
            )
        ).scalar()

    async def get_by_folder(
        self,
        folder_id: Optional[int],
        limit: int = 50,
        offset: int = 0,
    ) -> list[DocumentOrm]:
        stmt = (
            select(DocumentOrm)
            .where(DocumentOrm.folder_id == folder_id)
            .order_by(DocumentOrm.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return (await self.session.execute(stmt)).scalars().all()
