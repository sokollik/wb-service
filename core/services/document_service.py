import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from types_aiobotocore_s3 import S3Client

from core.common.common_exc import NotFoundHttpException
from core.common.common_repo import CommonRepository
from core.config.settings import get_settings
from core.exceptions.static_exc import (
    IncorrectFileTypeHttpException,
    UploadingFileTooBigHttpException,
)
from core.models.document import DocumentOrm
from core.models.enums import DocumentStatus
from core.repositories.document_repo import DocumentRepository
from core.schemas.document_schema import DocumentUpdateSchema
from core.utils.text_util import get_extension

settings = get_settings()

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image/jpeg",
    "image/png",
}

MAX_FILE_SIZE_MB = 50


class DocumentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.document_repo = DocumentRepository(session=session)
        self.common_repo = CommonRepository(session=session)

    async def get_document(self, doc_id: int) -> DocumentOrm:
        doc = await self.document_repo.get_by_id(doc_id)
        if not doc:
            raise NotFoundHttpException(name="document")
        return doc

    async def get_documents_by_folder(
        self,
        folder_id: int | None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DocumentOrm]:
        return await self.document_repo.get_by_folder(folder_id, limit, offset)

    async def upload(
        self,
        file: UploadFile,
        s3: S3Client,
        author_id: str,
        folder_id: int | None = None,
        title: str | None = None,
        description: str | None = None,
        curator_id: str | None = None,
    ) -> int:
        content = await file.read()
        size_mb = len(content) / 10**6
        if size_mb > MAX_FILE_SIZE_MB:
            raise UploadingFileTooBigHttpException()
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise IncorrectFileTypeHttpException(
                allowed_types=["pdf", "docx", "xlsx", "jpg", "png"],
            )

        file_ext = await get_extension(content_type=file.content_type)
        s3_key = f"documents/{uuid.uuid4()}.{file_ext}"

        await s3.put_object(
            Bucket=settings.MINIO_BUCKET,
            Key=s3_key,
            Body=content,
            ContentType=file.content_type,
        )

        doc_title = title or ".".join(file.filename.split(".")[:-1]) if file.filename else "untitled"

        doc = await self.common_repo.add(
            orm_instance=DocumentOrm(
                folder_id=folder_id,
                title=doc_title,
                type=file_ext,
                status=DocumentStatus.DRAFT,
                description=description,
                author_id=author_id,
                curator_id=curator_id,
                current_version=1,
                s3_key=s3_key,
                original_filename=file.filename or "unknown",
                file_size=len(content),
                mime_type=file.content_type,
            )
        )
        return doc.id

    async def update_document(
        self,
        doc_id: int,
        data: DocumentUpdateSchema,
    ) -> DocumentOrm:
        doc = await self.get_document(doc_id)
        update_data = data.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(doc, field, value)
        await self.session.flush()
        return doc

    async def generate_presigned_url(
        self,
        doc_id: int,
        s3: S3Client,
        expires_in: int = 10800, # 3 часа
        inline: bool = True,
    ) -> str:
        doc = await self.get_document(doc_id)
        disposition = "inline" if inline else "attachment"
        url = await s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.MINIO_BUCKET,
                "Key": doc.s3_key,
                "ResponseContentDisposition": f'{disposition}; filename="{doc.original_filename}"',
            },
            ExpiresIn=expires_in,
        )
        if settings.MINIO_EXTERNAL_ENDPOINT:
            url = url.replace(settings.MINIO_ENDPOINT, settings.MINIO_EXTERNAL_ENDPOINT, 1)
        return url

    async def delete_document(self, doc_id: int, s3: S3Client):
        doc = await self.get_document(doc_id)
        await s3.delete_object(Bucket=settings.MINIO_BUCKET, Key=doc.s3_key)
        await self.common_repo.delete(DocumentOrm, DocumentOrm.id == doc_id)
