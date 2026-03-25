from sqlalchemy import (
    BigInteger,
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

    current_version = Column(Integer, nullable=False, default=1)

    s3_key = Column(String, nullable=False, comment="UUID-ключ объекта в MinIO")

    original_filename = Column(String, nullable=False, comment="Оригинальное имя файла")

    file_size = Column(BigInteger, nullable=False, comment="Размер файла в байтах")

    mime_type = Column(String, nullable=False, comment="MIME-тип файла")

    created_at = Column(DateTime, server_default=func.now())

    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
