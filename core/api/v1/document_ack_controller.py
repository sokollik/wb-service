from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from fastapi_restful.cbv import cbv
from io import BytesIO
from sqlalchemy.ext.asyncio import AsyncSession
from core.services.document_export_service import DocumentExportService

from core.api.deps import CurrentUser, require_roles, CheckPermissionDep
from core.schemas.document_schema import (
    DocumentAcknowledgmentAssignSchema,
    DocumentAcknowledgmentListResponse,
    DocumentAcknowledgmentSchema,
    DocumentAcknowledgmentStatusSchema,
)
from core.services.document_acknowledgment_service import DocumentAcknowledgmentService
from core.utils.common_util import exception_handler
from core.utils.db_util import get_session_obj

document_ack_router = APIRouter(prefix="/documents", tags=["Document Acknowledgments"])


@cbv(document_ack_router)
class DocumentAcknowledgmentController:
    def __init__(self, session: AsyncSession = Depends(get_session_obj)):
        self.session = session
        self.ack_service = DocumentAcknowledgmentService(session=session)

    @document_ack_router.post(
        "/{document_id}/acknowledgment/assign",
        response_model=List[DocumentAcknowledgmentSchema],
    )
    @exception_handler
    async def assign_acknowledgment(
        self,
        document_id: int,
        data: DocumentAcknowledgmentAssignSchema,
        current_user: CurrentUser = Depends(CheckPermissionDep("documents", "manage", required_roles=["admin", "curator"])),
    ):
        return await self.ack_service.assign_acknowledgment(
            document_id=document_id,
            data=data,
            assigned_by=current_user.eid,
        )

    @document_ack_router.post(
        "/{document_id}/acknowledge",
        response_model=DocumentAcknowledgmentSchema,
    )
    @exception_handler
    async def acknowledge_document(
        self,
        document_id: int,
        employee_eid: str = Query(..., description="EID сотрудника, который ознакомился"),
        current_user: CurrentUser = Depends(CheckPermissionDep("documents", "read")),
    ):

        return await self.ack_service.acknowledge_document(
            document_id=document_id,
            employee_eid=employee_eid,
            acknowledged_by=current_user.eid,
        )

    @document_ack_router.get(
        "/{document_id}/acknowledgments",
        response_model=DocumentAcknowledgmentListResponse,
    )
    @exception_handler
    async def get_document_acknowledgments(
        self,
        document_id: int,
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        _current_user: CurrentUser = Depends(CheckPermissionDep("documents", "read")),
    ):
        return await self.ack_service.get_document_acknowledgments(
            document_id=document_id,
            limit=limit,
            offset=offset,
        )

    @document_ack_router.get(
        "/acknowledgments/employee/{employee_eid}",
        response_model=DocumentAcknowledgmentListResponse,
    )
    @exception_handler
    async def get_employee_acknowledgments(
        self,
        employee_eid: str,
        status: Optional[str] = Query(None, description="Статус: pending, acknowledged, overdue"),
        limit: int = Query(100, ge=1, le=1000),
        _current_user: CurrentUser = Depends(CheckPermissionDep("documents", "read", required_roles=["admin", "hr", "curator"])),
    ):
        
        return await self.ack_service.get_employee_acknowledgments(
            employee_eid=employee_eid,
            status=status,
            limit=limit,
        )

    @document_ack_router.get(
        "/acknowledgments/employee/{employee_eid}/status",
        response_model=DocumentAcknowledgmentStatusSchema,
    )
    @exception_handler
    async def get_employee_status(
        self,
        employee_eid: str,
        _current_user: CurrentUser = Depends(CheckPermissionDep("documents", "read", required_roles=["admin", "hr", "curator"])),
    ):

        return await self.ack_service.get_employee_status(employee_eid=employee_eid)

    @document_ack_router.delete(
        "/acknowledgments/{acknowledgment_id}",
    )
    @exception_handler
    async def delete_acknowledgment(
        self,
        acknowledgment_id: int,
        current_user: CurrentUser = Depends(CheckPermissionDep("documents", "manage", required_roles=["admin", "curator"])),
    ):

        return await self.ack_service.delete_acknowledgment(
            acknowledgment_id=acknowledgment_id,
            deleted_by=current_user.eid,
        )

    @document_ack_router.get(
        "/acknowledgments/export",
        response_class=StreamingResponse,
    )
    @exception_handler
    async def export_acknowledgments(
        self,
        document_id: Optional[int] = Query(None, description="ID документа для фильтрации"),
        employee_eid: Optional[str] = Query(None, description="EID сотрудника для фильтрации"),
        status: Optional[str] = Query(None, description="Статус: pending, acknowledged, overdue"),
        _current_user: CurrentUser = Depends(CheckPermissionDep("documents", "manage", required_roles=["admin", "curator"])),
    ):

        export_service = DocumentExportService(self.session)
        data = await self.ack_service.get_for_export(
            document_id=document_id,
            employee_eid=employee_eid,
            status=status,
        )
        
        excel_file = await export_service.create_acknowledgment_excel(data)
        
        return StreamingResponse(
            BytesIO(excel_file),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=document_acknowledgments.xlsx"
            },
        )
