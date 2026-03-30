<<<<<<< HEAD
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from core.models.base import Base
from core.models.enums import DocumentStatus


class FolderOrm(Base):
    __tablename__ = "folders"

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)

    name = Column(String, nullable=False, comment="Название папки")

    parent_id = Column(
        BigInteger,
        ForeignKey("folders.id", ondelete="CASCADE"),
        nullable=True,
        comment="Родительская папка",
    )

    path = Column(
        String,
        nullable=False,
        default="/",
        comment="Материализованный путь, например /1/5/12/",
        index=True,
    )

    created_by = Column(
        String,
        ForeignKey("employee.eid"),
        nullable=False,
        comment="Создатель папки",
    )

    created_at = Column(DateTime, server_default=func.now())


class DocumentOrm(Base):
    __tablename__ = "documents"

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)

    folder_id = Column(
        BigInteger,
        ForeignKey("folders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Папка, в которой лежит документ",
    )

    title = Column(String, nullable=False, comment="Название документа")

    type = Column(String, nullable=False, comment="Тип файла (pdf, docx, xlsx, ...)")

    status = Column(
        Enum(DocumentStatus),
        nullable=False,
        default=DocumentStatus.DRAFT,
        comment="Статус документа",
    )

    description = Column(Text, nullable=True, comment="Описание документа")

    author_id = Column(
        String,
        ForeignKey("employee.eid"),
        nullable=False,
        index=True,
        comment="Автор документа",
    )

    curator_id = Column(
        String,
        ForeignKey("employee.eid"),
        nullable=True,
        comment="Куратор документа",
    )

    s3_key = Column(String, nullable=False, comment="UUID-ключ объекта в MinIO")

    original_filename = Column(String, nullable=False, comment="Оригинальное имя файла")

    file_size = Column(BigInteger, nullable=False, comment="Размер файла в байтах")

    mime_type = Column(String, nullable=False, comment="MIME-тип файла")

    archived_at = Column(DateTime, nullable=True, comment="Дата архивирования")

    archived_by = Column(
        String,
        ForeignKey("employee.eid"),
        nullable=True,
        comment="Кто архивировал",
    )

    archive_comment = Column(String, nullable=True, comment="Основание архивирования")

    created_at = Column(DateTime, server_default=func.now())

    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class DocumentVersionOrm(Base):
    __tablename__ = "document_versions"

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)

    document_id = Column(
        BigInteger,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Документ, к которому относится версия",
    )

    version_major = Column(Integer, nullable=False, default=1, comment="Мажорная версия")

    version_minor = Column(Integer, nullable=False, default=0, comment="Минорная версия")

    s3_key = Column(String, nullable=False, comment="UUID-ключ объекта версии в MinIO")

    original_filename = Column(String, nullable=False, comment="Оригинальное имя файла версии")

    file_size = Column(BigInteger, nullable=False, comment="Размер файла версии в байтах")

    mime_type = Column(String, nullable=False, comment="MIME-тип файла версии")

    uploaded_by = Column(
        String,
        ForeignKey("employee.eid"),
        nullable=False,
        comment="Кто загрузил эту версию",
    )

    upload_comment = Column(String, nullable=True, comment="Комментарий к версии")

    is_current = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Является ли версия актуальной",
    )

    created_at = Column(DateTime, server_default=func.now())
=======
import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, DateTime, Boolean, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from core.models.base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(sa.BigInteger, primary_key=True, autoincrement=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    original_path = Column(String, nullable=False)
    original_extension = Column(String, nullable=False)
    original_mime_type = Column(String, nullable=False)
    original_size = Column(BigInteger, nullable=False)

    converted_path = Column(String, nullable=True)
    converted_at = Column(DateTime, nullable=True)
    conversion_status = Column(String, default="pending")
    conversion_error = Column(String, nullable=True)

    cache_key = Column(String, nullable=True, index=True)
    cache_expires_at = Column(DateTime, nullable=True)

    created_by = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    download_logs = relationship("DocumentDownloadLog", back_populates="document", cascade="all, delete-orphan")
    acknowledgments = relationship("DocumentAcknowledgment", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_documents_created_by_created_at", "created_by", "created_at"),
        Index("ix_documents_cache_expires", "cache_expires_at"),
    )


class DocumentAcknowledgment(Base):
    __tablename__ = "document_acknowledgments"

    id = Column(sa.BigInteger, primary_key=True, autoincrement=True, nullable=False)
    document_id = Column(sa.BigInteger, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    employee_eid = Column(String, nullable=False, index=True)
    
    required_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    acknowledged_at = Column(DateTime, nullable=True)
    
    acknowledged_by = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    document = relationship("Document", back_populates="acknowledgments")

    __table_args__ = (
        UniqueConstraint("document_id", "employee_eid", name="uq_document_employee"),
        Index("ix_acknowledgments_employee_eid", "employee_eid"),
        Index("ix_acknowledgments_acknowledged_at", "acknowledged_at"),
        Index("ix_acknowledgments_required_at", "required_at"),
    )


class DocumentDownloadLog(Base):
    __tablename__ = "document_download_logs"
    
    id = Column(sa.BigInteger, primary_key=True, autoincrement=True, nullable=False)
    document_id = Column(sa.BigInteger, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    user_id = Column(String, nullable=False, index=True)
    user_email = Column(String, nullable=True)
    user_username = Column(String, nullable=True)
    
    downloaded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    file_type = Column(String, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    user_agent = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    
    document = relationship("Document", back_populates="download_logs")
    
    __table_args__ = (
        Index("ix_download_logs_user_document", "user_id", "document_id"),
        Index("ix_download_logs_downloaded_at", "downloaded_at"),
    )


class ConversionTask(Base):
    __tablename__ = "conversion_tasks"
    
    id = Column(sa.BigInteger, primary_key=True, autoincrement=True, nullable=False)
    document_id = Column(sa.BigInteger, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    status = Column(String, default="pending", index=True)
    error_message = Column(String, nullable=True)
    
    queue_name = Column(String, default="document_conversion")
    task_id = Column(String, nullable=True, unique=True) 
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    document = relationship("Document", backref="conversion_task")
    
    __table_args__ = (
        Index("ix_conversion_tasks_status_created", "status", "created_at"),
    )
>>>>>>> main
