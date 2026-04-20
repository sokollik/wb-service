from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.models.document import (
    DocumentOrm,
    DocumentVersionOrm,
    DocumentDownloadLog,
    ConversionTask,
    DocumentAcknowledgment,
)
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
            pass
        else:
            stmt = stmt.where(DocumentOrm.status != DocumentStatus.ARCHIVED)

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


# Alias for backward compatibility
Document = DocumentOrm


class DocumentDownloadLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_download(
        self,
        document_id: int,
        user_id: str,
        file_type: str,
        file_size: int,
        user_email: Optional[str] = None,
        user_username: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> DocumentDownloadLog:
        log = DocumentDownloadLog(
            document_id=document_id,
            user_id=user_id,
            user_email=user_email,
            user_username=user_username,
            file_type=file_type,
            file_size=file_size,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)
        return log

    async def get_logs_by_document(
        self,
        document_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[DocumentDownloadLog], int]:
        count_result = await self.session.execute(
            select(func.count()).where(DocumentDownloadLog.document_id == document_id)
        )
        total = count_result.scalar()

        result = await self.session.execute(
            select(DocumentDownloadLog)
            .where(DocumentDownloadLog.document_id == document_id)
            .order_by(desc(DocumentDownloadLog.downloaded_at))
            .limit(limit)
            .offset(offset)
        )
        logs = result.scalars().all()
        return list(logs), total

    async def get_logs_by_user(
        self,
        user_id: str,
        limit: int = 100,
    ) -> list[DocumentDownloadLog]:
        result = await self.session.execute(
            select(DocumentDownloadLog)
            .where(DocumentDownloadLog.user_id == user_id)
            .order_by(desc(DocumentDownloadLog.downloaded_at))
            .limit(limit)
        )
        return list(result.scalars().all())


class DocumentAcknowledgmentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_acknowledgment(
        self,
        document_id: int,
        employee_eid: str,
        required_at: datetime,
    ) -> DocumentAcknowledgment:
        acknowledgment = DocumentAcknowledgment(
            document_id=document_id,
            employee_eid=employee_eid,
            required_at=required_at,
        )
        self.session.add(acknowledgment)
        await self.session.flush()
        await self.session.refresh(acknowledgment)
        return acknowledgment

    async def get_by_document(
        self,
        document_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[DocumentAcknowledgment], int]:
        count_result = await self.session.execute(
            select(func.count()).where(DocumentAcknowledgment.document_id == document_id)
        )
        total = count_result.scalar()

        result = await self.session.execute(
            select(DocumentAcknowledgment)
            .where(DocumentAcknowledgment.document_id == document_id)
            .order_by(desc(DocumentAcknowledgment.required_at))
            .limit(limit)
            .offset(offset)
        )
        acknowledgments = result.scalars().all()
        return list(acknowledgments), total

    async def get_by_employee(
        self,
        employee_eid: str,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[DocumentAcknowledgment]:
        query = select(DocumentAcknowledgment).where(
            DocumentAcknowledgment.employee_eid == employee_eid
        )

        if status == "pending":
            query = query.where(DocumentAcknowledgment.acknowledged_at.is_(None))
        elif status == "acknowledged":
            query = query.where(DocumentAcknowledgment.acknowledged_at.isnot(None))
        elif status == "overdue":
            query = query.where(
                DocumentAcknowledgment.acknowledged_at.is_(None),
                DocumentAcknowledgment.required_at < datetime.utcnow(),
            )

        query = query.order_by(desc(DocumentAcknowledgment.required_at)).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, acknowledgment_id: int) -> Optional[DocumentAcknowledgment]:
        result = await self.session.execute(
            select(DocumentAcknowledgment).where(DocumentAcknowledgment.id == acknowledgment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_document_and_employee(
        self,
        document_id: int,
        employee_eid: str,
    ) -> Optional[DocumentAcknowledgment]:
        result = await self.session.execute(
            select(DocumentAcknowledgment).where(
                DocumentAcknowledgment.document_id == document_id,
                DocumentAcknowledgment.employee_eid == employee_eid,
            )
        )
        return result.scalar_one_or_none()

    async def acknowledge(
        self,
        acknowledgment_id: int,
        acknowledged_by: str,
    ) -> Optional[DocumentAcknowledgment]:
        acknowledgment = await self.get_by_id(acknowledgment_id)
        if acknowledgment:
            acknowledgment.acknowledged_at = datetime.utcnow()
            acknowledgment.acknowledged_by = acknowledged_by
            await self.session.flush()
            await self.session.refresh(acknowledgment)
        return acknowledgment

    async def acknowledge_by_document_and_employee(
        self,
        document_id: int,
        employee_eid: str,
        acknowledged_by: str,
    ) -> Optional[DocumentAcknowledgment]:
        acknowledgment = await self.get_by_document_and_employee(document_id, employee_eid)
        if acknowledgment:
            acknowledgment.acknowledged_at = datetime.utcnow()
            acknowledgment.acknowledged_by = acknowledged_by
            await self.session.flush()
            await self.session.refresh(acknowledgment)
        return acknowledgment

    async def delete_acknowledgment(
        self,
        acknowledgment_id: int,
    ) -> bool:
        acknowledgment = await self.get_by_id(acknowledgment_id)
        if acknowledgment:
            await self.session.delete(acknowledgment)
            await self.session.flush()
            return True
        return False

    async def get_status_by_employee(
        self,
        employee_eid: str,
    ) -> dict:
        total_result = await self.session.execute(
            select(func.count()).where(DocumentAcknowledgment.employee_eid == employee_eid)
        )
        total = total_result.scalar() or 0

        acknowledged_result = await self.session.execute(
            select(func.count()).where(
                DocumentAcknowledgment.employee_eid == employee_eid,
                DocumentAcknowledgment.acknowledged_at.isnot(None),
            )
        )
        acknowledged = acknowledged_result.scalar() or 0

        overdue_result = await self.session.execute(
            select(func.count()).where(
                DocumentAcknowledgment.employee_eid == employee_eid,
                DocumentAcknowledgment.acknowledged_at.is_(None),
                DocumentAcknowledgment.required_at < datetime.utcnow(),
            )
        )
        overdue = overdue_result.scalar() or 0

        pending = total - acknowledged

        return {
            "employee_eid": employee_eid,
            "total_documents": total,
            "acknowledged_count": acknowledged,
            "pending_count": pending,
            "overdue_count": overdue,
        }

    async def get_for_export(
        self,
        document_id: Optional[int] = None,
        employee_eid: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 1000,
    ) -> List[DocumentAcknowledgment]:
        query = select(DocumentAcknowledgment).options(
            selectinload(DocumentAcknowledgment.document)
        )

        if document_id:
            query = query.where(DocumentAcknowledgment.document_id == document_id)
        if employee_eid:
            query = query.where(DocumentAcknowledgment.employee_eid == employee_eid)
        if status == "pending":
            query = query.where(DocumentAcknowledgment.acknowledged_at.is_(None))
        elif status == "acknowledged":
            query = query.where(DocumentAcknowledgment.acknowledged_at.isnot(None))
        elif status == "overdue":
            query = query.where(
                DocumentAcknowledgment.acknowledged_at.is_(None),
                DocumentAcknowledgment.required_at < datetime.utcnow(),
            )

        query = query.order_by(
            desc(DocumentAcknowledgment.required_at),
            DocumentAcknowledgment.employee_eid,
        ).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())


class ConversionTaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(
        self,
        document_id: int,
        task_id: Optional[str] = None,
    ) -> ConversionTask:
        task = ConversionTask(
            document_id=document_id,
            task_id=task_id,
            status="pending",
        )
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def get_by_document_id(
        self,
        document_id: int,
    ) -> Optional[ConversionTask]:
        result = await self.session.execute(
            select(ConversionTask)
            .where(ConversionTask.document_id == document_id)
            .order_by(desc(ConversionTask.created_at))
        )
        return result.scalar_one_or_none()

    async def get_by_task_id(
        self,
        task_id: str,
    ) -> Optional[ConversionTask]:
        result = await self.session.execute(
            select(ConversionTask).where(ConversionTask.task_id == task_id)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        task_id: int,
        status: str,
        error_message: Optional[str] = None,
    ) -> Optional[ConversionTask]:
        result = await self.session.execute(
            select(ConversionTask).where(ConversionTask.id == task_id)
        )
        task = result.scalar_one_or_none()

        if task:
            task.status = status
            task.error_message = error_message
            if status == "processing" and not task.started_at:
                task.started_at = datetime.utcnow()
            elif status in ("completed", "failed") and not task.completed_at:
                task.completed_at = datetime.utcnow()
            await self.session.flush()
            await self.session.refresh(task)
        return task

    async def get_pending_tasks(
        self,
        limit: int = 10,
    ) -> list[ConversionTask]:
        result = await self.session.execute(
            select(ConversionTask)
            .where(ConversionTask.status == "pending")
            .order_by(ConversionTask.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())
