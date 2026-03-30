from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.common.common_exc import NotFoundException, ForbiddenHttpException
from core.models.rbac import RoleEnum
from core.repositories.document_repo import DocumentAcknowledgmentRepository, DocumentRepository
from core.schemas.document_schema import (
    DocumentAcknowledgmentAssignSchema,
    DocumentAcknowledgmentDetailSchema,
    DocumentAcknowledgmentExportSchema,
    DocumentAcknowledgmentListResponse,
    DocumentAcknowledgmentSchema,
    DocumentAcknowledgmentStatusSchema,
)
from core.services.rbac_service import RBACService
from core.services.notification_event_service import NotificationEventService


class DocumentAcknowledgmentService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.acknowledgment_repo = DocumentAcknowledgmentRepository(session)
        self.document_repo = DocumentRepository(session)
        self.rbac_service = RBACService(session)
        self.notification_service = NotificationEventService(session)

    async def assign_acknowledgment(
        self,
        document_id: int,
        data: DocumentAcknowledgmentAssignSchema,
        assigned_by: str,
    ) -> List[DocumentAcknowledgmentSchema]:

        document = await self.document_repo.get_by_id(document_id)
        if not document:
            raise NotFoundException(name="document", id=document_id)

        has_permission = await self.rbac_service.check_role(
            assigned_by, [RoleEnum.ADMIN, RoleEnum.CURATOR]
        )
        if not has_permission and document.created_by != assigned_by:
            raise ForbiddenHttpException(detail="Нет прав для назначения ознакомления")

        created_acknowledgments = []
        required_at = data.required_at or datetime.utcnow()

        for employee_eid in data.employee_eids:
            existing = await self.acknowledgment_repo.get_by_document_and_employee(
                document_id, employee_eid
            )
            if existing:
                if not existing.acknowledged_at:
                    existing.required_at = required_at
                    created_acknowledgments.append(
                        DocumentAcknowledgmentSchema.model_validate(existing)
                    )
                continue

            acknowledgment = await self.acknowledgment_repo.create_acknowledgment(
                document_id=document_id,
                employee_eid=employee_eid,
                required_at=required_at,
            )
            created_acknowledgments.append(
                DocumentAcknowledgmentSchema.model_validate(acknowledgment)
            )

            await self.notification_service.notify_acknowledgment_assigned(
                document_id=document_id,
                document_name=document.name,
                employee_eid=employee_eid,
                required_at=required_at,
                assigned_by=assigned_by,
            )

        return created_acknowledgments

    async def acknowledge_document(
        self,
        document_id: int,
        employee_eid: str,
        acknowledged_by: str,
    ) -> DocumentAcknowledgmentSchema:

        document = await self.document_repo.get_by_id(document_id)
        if not document:
            raise NotFoundException(name="document", id=document_id)

        acknowledgment = await self.acknowledgment_repo.get_by_document_and_employee(
            document_id, employee_eid
        )
        if not acknowledgment:
            raise NotFoundException(
                detail=f"Ознакомление для документа {document_id} и сотрудника {employee_eid} не найдено"
            )

        if acknowledgment.acknowledged_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Документ уже был ознакомлен",
            )

        acknowledgment = await self.acknowledgment_repo.acknowledge(
            acknowledgment_id=acknowledgment.id,
            acknowledged_by=acknowledged_by,
        )

        return DocumentAcknowledgmentSchema.model_validate(acknowledgment)

    async def get_document_acknowledgments(
        self,
        document_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> DocumentAcknowledgmentListResponse:

        acknowledgments, total = await self.acknowledgment_repo.get_by_document(
            document_id=document_id,
            limit=limit,
            offset=offset,
        )

        document = await self.document_repo.get_by_id(document_id)
        document_name = document.name if document else "Unknown"

        detailed_acknowledgments = []
        for ack in acknowledgments:
            is_overdue = (
                not ack.acknowledged_at and 
                ack.required_at < datetime.utcnow()
            )
            detailed_acknowledgments.append(
                DocumentAcknowledgmentDetailSchema(
                    id=ack.id,
                    document_id=ack.document_id,
                    employee_eid=ack.employee_eid,
                    required_at=ack.required_at,
                    acknowledged_at=ack.acknowledged_at,
                    acknowledged_by=ack.acknowledged_by,
                    created_at=ack.created_at,
                    document_name=document_name,
                    is_overdue=is_overdue,
                )
            )

        return DocumentAcknowledgmentListResponse(
            total=total,
            acknowledgments=detailed_acknowledgments,
        )

    async def get_employee_acknowledgments(
        self,
        employee_eid: str,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> DocumentAcknowledgmentListResponse:

        acknowledgments = await self.acknowledgment_repo.get_by_employee(
            employee_eid=employee_eid,
            status=status,
            limit=limit,
        )

        detailed_acknowledgments = []
        for ack in acknowledgments:
            document = await self.document_repo.get_by_id(ack.document_id)
            document_name = document.name if document else "Unknown"
            is_overdue = (
                not ack.acknowledged_at and 
                ack.required_at < datetime.utcnow()
            )
            detailed_acknowledgments.append(
                DocumentAcknowledgmentDetailSchema(
                    id=ack.id,
                    document_id=ack.document_id,
                    employee_eid=ack.employee_eid,
                    required_at=ack.required_at,
                    acknowledged_at=ack.acknowledged_at,
                    acknowledged_by=ack.acknowledged_by,
                    created_at=ack.created_at,
                    document_name=document_name,
                    is_overdue=is_overdue,
                )
            )

        return DocumentAcknowledgmentListResponse(
            total=len(acknowledgments),
            acknowledgments=detailed_acknowledgments,
        )

    async def get_employee_status(
        self,
        employee_eid: str,
    ) -> DocumentAcknowledgmentStatusSchema:

        status_data = await self.acknowledgment_repo.get_status_by_employee(employee_eid)
        return DocumentAcknowledgmentStatusSchema(**status_data)

    async def delete_acknowledgment(
        self,
        acknowledgment_id: int,
        deleted_by: str,
    ) -> bool:

        has_permission = await self.rbac_service.check_role(
            deleted_by, [RoleEnum.ADMIN, RoleEnum.CURATOR]
        )
        if not has_permission:
            raise ForbiddenHttpException(detail="Нет прав для удаления ознакомления")

        acknowledgment = await self.acknowledgment_repo.get_by_id(acknowledgment_id)
        if not acknowledgment:
            raise NotFoundException(name="acknowledgment", id=acknowledgment_id)

        return await self.acknowledgment_repo.delete_acknowledgment(acknowledgment_id)

    async def get_for_export(
        self,
        document_id: Optional[int] = None,
        employee_eid: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[DocumentAcknowledgmentExportSchema]:

        acknowledgments = await self.acknowledgment_repo.get_for_export(
            document_id=document_id,
            employee_eid=employee_eid,
            status=status,
        )

        export_data = []
        for ack in acknowledgments:
            document = await self.document_repo.get_by_id(ack.document_id)
            document_name = document.name if document else "Unknown"
            
            is_overdue = (
                not ack.acknowledged_at and 
                ack.required_at < datetime.utcnow()
            )
            
            if ack.acknowledged_at:
                ack_status = "acknowledged"
            elif is_overdue:
                ack_status = "overdue"
            else:
                ack_status = "pending"

            employee_full_name = None
            try:
                from core.models.emploee import EmployeeOrm
                employee = await self.session.get(EmployeeOrm, ack.employee_eid)
                if employee:
                    employee_full_name = employee.full_name
            except Exception:
                pass

            export_data.append(
                DocumentAcknowledgmentExportSchema(
                    id=ack.id,
                    document_id=ack.document_id,
                    document_name=document_name,
                    employee_eid=ack.employee_eid,
                    employee_full_name=employee_full_name,
                    required_at=ack.required_at,
                    acknowledged_at=ack.acknowledged_at,
                    acknowledged_by=ack.acknowledged_by,
                    status=ack_status,
                    is_overdue=is_overdue,
                )
            )

        return export_data
