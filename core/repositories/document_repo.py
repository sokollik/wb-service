from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.document import DocumentOrm, DocumentVersionOrm
from core.models.enums import DocumentStatus


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
        show_archived: bool = False,
        current_user_eid: str | None = None,
        is_privileged: bool = False,
    ) -> list[DocumentOrm]:
        stmt = select(DocumentOrm).where(DocumentOrm.folder_id == folder_id)

        if show_archived:
            # показываем все статусы включая архив
            pass
        else:
            stmt = stmt.where(DocumentOrm.status != DocumentStatus.ARCHIVED)

        # DRAFT виден только автору/куратору, hr и admin видят все
        if not is_privileged and current_user_eid:
            stmt = stmt.where(
                or_(
                    DocumentOrm.status != DocumentStatus.DRAFT,
                    DocumentOrm.author_id == current_user_eid,
                    DocumentOrm.curator_id == current_user_eid,
                )
            )

        stmt = stmt.order_by(DocumentOrm.created_at.desc()).limit(limit).offset(offset)
        return (await self.session.execute(stmt)).scalars().all()


class DocumentVersionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_document(self, doc_id: int) -> list[DocumentVersionOrm]:
        stmt = (
            select(DocumentVersionOrm)
            .where(DocumentVersionOrm.document_id == doc_id)
            .order_by(
                DocumentVersionOrm.version_major.desc(),
                DocumentVersionOrm.version_minor.desc(),
            )
        )
        return (await self.session.execute(stmt)).scalars().all()

    async def get_by_id(self, version_id: int) -> Optional[DocumentVersionOrm]:
        return (
            await self.session.execute(
                select(DocumentVersionOrm).where(DocumentVersionOrm.id == version_id)
            )
        ).scalar()

    async def get_latest(self, doc_id: int) -> Optional[DocumentVersionOrm]:
        stmt = (
            select(DocumentVersionOrm)
            .where(DocumentVersionOrm.document_id == doc_id)
            .order_by(
                DocumentVersionOrm.version_major.desc(),
                DocumentVersionOrm.version_minor.desc(),
            )
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar()
