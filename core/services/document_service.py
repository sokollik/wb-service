import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from types_aiobotocore_s3 import S3Client

from core.common.common_exc import NotAllowedHttpException, NotFoundHttpException
from core.common.common_repo import CommonRepository
from core.config.settings import get_settings
from core.exceptions.static_exc import (
    IncorrectFileTypeHttpException,
    UploadingFileTooBigHttpException,
)
from core.models.document import DocumentOrm, DocumentVersionOrm
from core.models.enums import DocumentStatus
from core.repositories.document_repo import DocumentRepository, DocumentVersionRepository
from core.schemas.document_schema import DocumentUpdateSchema
from core.services.document_es_service import DocumentElasticsearchService
from core.utils.text_extractor import extract_text
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
    def __init__(
        self,
        session: AsyncSession,
        es: DocumentElasticsearchService | None = None,
    ):
        self.session = session
        self.es = es
        self.document_repo = DocumentRepository(session=session)
        self.version_repo = DocumentVersionRepository(session=session)
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
        show_archived: bool = False,
        current_user_eid: str | None = None,
        is_privileged: bool = False,
    ) -> list[DocumentOrm]:
        return await self.document_repo.get_by_folder(
            folder_id,
            limit,
            offset,
            show_archived=show_archived,
            current_user_eid=current_user_eid,
            is_privileged=is_privileged,
        )

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
                s3_key=s3_key,
                original_filename=file.filename or "unknown",
                file_size=len(content),
                mime_type=file.content_type,
            )
        )

        await self.common_repo.add(
            orm_instance=DocumentVersionOrm(
                document_id=doc.id,
                version_major=1,
                version_minor=0,
                s3_key=s3_key,
                original_filename=file.filename or "unknown",
                file_size=len(content),
                mime_type=file.content_type,
                uploaded_by=author_id,
                is_current=True,
            )
        )

        if self.es:
            await self.session.refresh(doc)
            content_text = extract_text(content, file.content_type)
            self.es.index_document({
                "doc_id": str(doc.id),
                "title": doc.title,
                "content": content_text or "",
                "type": doc.type,
                "status": doc.status.value,
                "author_id": doc.author_id,
                "curator_id": doc.curator_id or "",
                "folder_id": str(doc.folder_id) if doc.folder_id else "",
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
            })

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
        await self.session.refresh(doc)
        if self.es:
            es_fields = {
                k: (v.value if hasattr(v, "value") else v)
                for k, v in update_data.items()
            }
            es_fields["updated_at"] = doc.updated_at.isoformat() if doc.updated_at else None
            self.es.update_document_meta(doc_id, es_fields)
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
        await self.get_document(doc_id)
        versions = await self.version_repo.get_by_document(doc_id)
        for v in versions:
            await s3.delete_object(Bucket=settings.MINIO_BUCKET, Key=v.s3_key)
        await self.common_repo.delete(DocumentOrm, DocumentOrm.id == doc_id)
        if self.es:
            self.es.delete_document(doc_id)

    # ── Версии ──────────────────────────────────────────────────────────────

    async def get_versions(self, doc_id: int) -> list[DocumentVersionOrm]:
        await self.get_document(doc_id)
        return await self.version_repo.get_by_document(doc_id)

    async def upload_version(
        self,
        doc_id: int,
        file: UploadFile,
        s3: S3Client,
        uploaded_by: str,
        current_user_roles: list[str],
        upload_comment: str | None = None,
        bump_major: bool = False,
    ) -> DocumentVersionOrm:
        doc = await self.get_document(doc_id)

        is_privileged = any(r in current_user_roles for r in ["hr", "admin"])
        is_curator = doc.curator_id == uploaded_by
        if not is_privileged and not is_curator:
            raise NotAllowedHttpException()

        content = await file.read()
        if len(content) / 10**6 > MAX_FILE_SIZE_MB:
            raise UploadingFileTooBigHttpException()
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise IncorrectFileTypeHttpException(
                allowed_types=["pdf", "docx", "xlsx", "jpg", "png"]
            )

        file_ext = await get_extension(content_type=file.content_type)
        s3_key = f"documents/{uuid.uuid4()}.{file_ext}"
        await s3.put_object(
            Bucket=settings.MINIO_BUCKET,
            Key=s3_key,
            Body=content,
            ContentType=file.content_type,
        )

        latest = await self.version_repo.get_latest(doc_id)
        if latest is None:
            new_major, new_minor = 1, 0
        elif bump_major:
            new_major, new_minor = latest.version_major + 1, 0
        else:
            new_major, new_minor = latest.version_major, latest.version_minor + 1

        await self.common_repo.update_stmt(
            DocumentVersionOrm,
            DocumentVersionOrm.document_id == doc_id,
            {"is_current": False},
        )

        new_version = await self.common_repo.add(
            orm_instance=DocumentVersionOrm(
                document_id=doc_id,
                version_major=new_major,
                version_minor=new_minor,
                s3_key=s3_key,
                original_filename=file.filename or "unknown",
                file_size=len(content),
                mime_type=file.content_type,
                uploaded_by=uploaded_by,
                upload_comment=upload_comment,
                is_current=True,
            )
        )

        doc.s3_key = s3_key
        doc.original_filename = file.filename or "unknown"
        doc.file_size = len(content)
        doc.mime_type = file.content_type
        await self.session.flush()

        return new_version

    async def set_current_version(
        self, doc_id: int, version_id: int
    ) -> DocumentVersionOrm:
        await self.get_document(doc_id)
        version = await self.version_repo.get_by_id(version_id)
        if not version or version.document_id != doc_id:
            raise NotFoundHttpException(name="version")

        await self.common_repo.update_stmt(
            DocumentVersionOrm,
            DocumentVersionOrm.document_id == doc_id,
            {"is_current": False},
        )
        version.is_current = True
        await self.session.flush()
        return version

    async def download_version(
        self, doc_id: int, version_id: int, s3: S3Client
    ) -> str:
        await self.get_document(doc_id)
        version = await self.version_repo.get_by_id(version_id)
        if not version or version.document_id != doc_id:
            raise NotFoundHttpException(name="version")

        url = await s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.MINIO_BUCKET,
                "Key": version.s3_key,
                "ResponseContentDisposition": f'attachment; filename="{version.original_filename}"',
            },
            ExpiresIn=10800,
        )
        if settings.MINIO_EXTERNAL_ENDPOINT:
            url = url.replace(settings.MINIO_ENDPOINT, settings.MINIO_EXTERNAL_ENDPOINT, 1)
        return url

    async def delete_version(
        self,
        doc_id: int,
        version_id: int,
        s3: S3Client,
        deleter_eid: str,
        deleter_roles: list[str],
        reason: str,
    ):
        doc = await self.get_document(doc_id)

        is_admin = "admin" in deleter_roles
        is_curator = doc.curator_id == deleter_eid
        if not is_admin and not is_curator:
            raise NotAllowedHttpException()

        version = await self.version_repo.get_by_id(version_id)
        if not version or version.document_id != doc_id:
            raise NotFoundHttpException(name="version")

        logger.info(
            "Version %s of document %s deleted by %s. Reason: %s",
            version_id, doc_id, deleter_eid, reason,
        )
        await s3.delete_object(Bucket=settings.MINIO_BUCKET, Key=version.s3_key)
        await self.common_repo.delete(DocumentVersionOrm, DocumentVersionOrm.id == version_id)

    # ── Архивирование ────────────────────────────────────────────────────────

    async def archive_document(
        self,
        doc_id: int,
        archived_by: str,
        comment: str,
    ) -> DocumentOrm:
        doc = await self.get_document(doc_id)
        if doc.status == DocumentStatus.ARCHIVED:
            raise NotAllowedHttpException()
        doc.status = DocumentStatus.ARCHIVED
        doc.archived_at = datetime.utcnow()
        doc.archived_by = archived_by
        doc.archive_comment = comment
        await self.session.flush()
        await self.session.refresh(doc)
        if self.es:
            self.es.update_document_meta(doc_id, {"status": DocumentStatus.ARCHIVED.value})
        return doc

    async def restore_document(self, doc_id: int) -> DocumentOrm:
        doc = await self.get_document(doc_id)
        if doc.status != DocumentStatus.ARCHIVED:
            raise NotAllowedHttpException()
        doc.status = DocumentStatus.ACTIVE
        doc.archived_at = None
        doc.archived_by = None
        doc.archive_comment = None
        await self.session.flush()
        await self.session.refresh(doc)
        if self.es:
            self.es.update_document_meta(doc_id, {"status": DocumentStatus.ACTIVE.value})
        return doc
