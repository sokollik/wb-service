from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi_restful.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession
from types_aiobotocore_s3 import S3Client

from core.api.deps import CurrentUser, require_roles
from core.schemas.document_schema import DocumentSchema, DocumentUpdateSchema
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
    ):
        self.session = session
        self.s3 = s3
        self.document_service = DocumentService(session=session)

    @document_router.get("/", response_model=List[DocumentSchema])
    @exception_handler
    async def get_documents(
        self,
        _current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
        folder_id: Optional[int] = Query(None),
        page: int = Query(1, ge=1),
        size: int = Query(50, ge=1, le=100),
    ):
        offset = (page - 1) * size
        return await self.document_service.get_documents_by_folder(
            folder_id=folder_id, limit=size, offset=offset
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
