from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi_restful.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession
from types_aiobotocore_s3 import S3Client

from core.api.deps import CurrentUser, require_roles
from core.schemas.document_schema import (
    DocumentArchiveSchema,
    DocumentSchema,
    DocumentSearchResponse,
    DocumentUpdateSchema,
    DocumentVersionSchema,
)
from core.services.document_es_service import DocumentElasticsearchService
from core.utils.elastic_search_util import get_document_es_service
from core.services.document_service import DocumentService
from core.utils.common_util import exception_handler
from core.utils.db_util import get_session_obj
from core.utils.s3_util import get_s3_dep

document_router = APIRouter(tags=["Documents"])


@cbv(document_router)
class DocumentController:
    def __init__(
        self,
        session: AsyncSession = Depends(get_session_obj),
        s3: S3Client = Depends(get_s3_dep),
        es: DocumentElasticsearchService = Depends(get_document_es_service),
    ):
        self.session = session
        self.s3 = s3
        self.document_service = DocumentService(session=session, es=es)

    @document_router.get("/", response_model=List[DocumentSchema])
    @exception_handler
    async def get_documents(
        self,
        current_user: CurrentUser = Depends(require_roles(["employee", "hr", "admin", "news_editor"])),
        folder_id: Optional[int] = Query(None),
        show_archived: bool = Query(False),
        page: int = Query(1, ge=1),
        size: int = Query(50, ge=1, le=100),
    ):
        offset = (page - 1) * size
        is_privileged = any(r in current_user.roles for r in ["hr", "admin"])
        return await self.document_service.get_documents_by_folder(
            folder_id=folder_id,
            limit=size,
            offset=offset,
            show_archived=show_archived,
            current_user_eid=current_user.eid,
            is_privileged=is_privileged,
        )

    @document_router.get("/search", response_model=DocumentSearchResponse)
    @exception_handler
    async def search_documents(
        self,
        _current_user: CurrentUser = Depends(require_roles(["employee", "hr", "admin"])),
        q: Optional[str] = Query(None, description="Поисковый запрос"),
        doc_type: Optional[str] = Query(None, description="Тип файла: pdf, docx, xlsx..."),
        status: Optional[str] = Query(None, description="Статус: DRAFT, ACTIVE, ARCHIVED"),
        author_id: Optional[str] = Query(None),
        curator_id: Optional[str] = Query(None),
        date_from: Optional[str] = Query(None, description="Дата от (ISO 8601)"),
        date_to: Optional[str] = Query(None, description="Дата до (ISO 8601)"),
        show_archived: bool = Query(False),
        from_: int = Query(0, ge=0),
        size: int = Query(20, ge=1, le=100),
    ):
        from datetime import datetime as dt
        parsed_from = dt.fromisoformat(date_from) if date_from else None
        parsed_to = dt.fromisoformat(date_to) if date_to else None
        return self.document_service.es.search_documents(
            query=q,
            doc_type=doc_type,
            status=status,
            author_id=author_id,
            curator_id=curator_id,
            date_from=parsed_from,
            date_to=parsed_to,
            show_archived=show_archived,
            from_=from_,
            size=size,
        )

    @document_router.get("/{doc_id}", response_model=DocumentSchema)
    @exception_handler
    async def get_document(
        self,
        doc_id: int,
        _current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
    ):
        return await self.document_service.get_document(doc_id)

    @document_router.get("/{doc_id}/download")
    @exception_handler
    async def get_download_url(
        self,
        doc_id: int,
        _current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
    ):
        url = await self.document_service.generate_presigned_url(
            doc_id=doc_id, s3=self.s3
        )
        return {"url": url}

    @document_router.post("/upload", response_model=int)
    @exception_handler
    async def upload_document(
        self,
        file: UploadFile = File(...),
        current_user: CurrentUser = Depends(require_roles(["hr", "admin"])),
        folder_id: Optional[int] = Form(None),
        title: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        curator_id: Optional[str] = Form(None),
    ):
        return await self.document_service.upload(
            file=file,
            s3=self.s3,
            author_id=current_user.eid,
            folder_id=folder_id,
            title=title,
            description=description,
            curator_id=curator_id,
        )

    @document_router.patch("/{doc_id}", response_model=DocumentSchema)
    @exception_handler
    async def update_document(
        self,
        doc_id: int,
        data: DocumentUpdateSchema,
        _current_user: CurrentUser = Depends(require_roles(["hr", "admin"])),
    ):
        return await self.document_service.update_document(doc_id, data)

    @document_router.delete("/{doc_id}")
    @exception_handler
    async def delete_document(
        self,
        doc_id: int,
        _current_user: CurrentUser = Depends(require_roles(["hr", "admin"])),
    ):
        await self.document_service.delete_document(doc_id, self.s3)

    @document_router.put("/{doc_id}/archive", response_model=DocumentSchema)
    @exception_handler
    async def archive_document(
        self,
        doc_id: int,
        data: DocumentArchiveSchema,
        current_user: CurrentUser = Depends(require_roles(["hr", "admin"])),
    ):
        return await self.document_service.archive_document(
            doc_id=doc_id,
            archived_by=current_user.eid,
            comment=data.comment,
        )

    @document_router.put("/{doc_id}/restore", response_model=DocumentSchema)
    @exception_handler
    async def restore_document(
        self,
        doc_id: int,
        _current_user: CurrentUser = Depends(require_roles(["hr", "admin"])),
    ):
        return await self.document_service.restore_document(doc_id)

    # ── Версии ──────────────────────────────────────────────────────────────

    @document_router.get("/{doc_id}/versions", response_model=List[DocumentVersionSchema])
    @exception_handler
    async def get_versions(
        self,
        doc_id: int,
        _current_user: CurrentUser = Depends(require_roles(["employee", "hr", "admin"])),
    ):
        return await self.document_service.get_versions(doc_id)

    @document_router.post("/{doc_id}/versions", response_model=DocumentVersionSchema)
    @exception_handler
    async def upload_version(
        self,
        doc_id: int,
        file: UploadFile = File(...),
        current_user: CurrentUser = Depends(require_roles(["employee", "hr", "admin"])),
        upload_comment: Optional[str] = Form(None),
        bump_major: bool = Form(False),
    ):
        return await self.document_service.upload_version(
            doc_id=doc_id,
            file=file,
            s3=self.s3,
            uploaded_by=current_user.eid,
            current_user_roles=current_user.roles,
            upload_comment=upload_comment,
            bump_major=bump_major,
        )

    @document_router.get("/{doc_id}/versions/{version_id}/download")
    @exception_handler
    async def download_version(
        self,
        doc_id: int,
        version_id: int,
        _current_user: CurrentUser = Depends(require_roles(["employee", "hr", "admin"])),
    ):
        url = await self.document_service.download_version(
            doc_id=doc_id, version_id=version_id, s3=self.s3
        )
        return {"url": url}

    @document_router.patch("/{doc_id}/versions/{version_id}/set-current", response_model=DocumentVersionSchema)
    @exception_handler
    async def set_current_version(
        self,
        doc_id: int,
        version_id: int,
        _current_user: CurrentUser = Depends(require_roles(["hr", "admin"])),
    ):
        return await self.document_service.set_current_version(doc_id, version_id)

    @document_router.delete("/{doc_id}/versions/{version_id}")
    @exception_handler
    async def delete_version(
        self,
        doc_id: int,
        version_id: int,
        current_user: CurrentUser = Depends(require_roles(["employee", "hr", "admin"])),
        reason: str = Query(..., min_length=1, description="Основание для удаления версии"),
    ):
        await self.document_service.delete_version(
            doc_id=doc_id,
            version_id=version_id,
            s3=self.s3,
            deleter_eid=current_user.eid,
            deleter_roles=current_user.roles,
            reason=reason,
        )
