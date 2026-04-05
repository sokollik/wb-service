from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, computed_field

from core.models.enums import DocumentStatus


class DocumentSchema(BaseModel):
    id: int
    folder_id: Optional[int] = None
    title: str
    type: str
    status: DocumentStatus
    description: Optional[str] = None
    author_id: str
    curator_id: Optional[str] = None
    original_filename: str
    file_size: int
    mime_type: str
    archived_at: Optional[datetime] = None
    archived_by: Optional[str] = None
    archive_comment: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentArchiveSchema(BaseModel):
    comment: str = Field(..., min_length=1, max_length=500)


class DocumentUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    folder_id: Optional[int] = None
    status: Optional[DocumentStatus] = None
    description: Optional[str] = None
    curator_id: Optional[str] = None


class DocumentVersionSchema(BaseModel):
    id: int
    document_id: int
    version_major: int
    version_minor: int
    original_filename: str
    file_size: int
    mime_type: str
    uploaded_by: str
    upload_comment: Optional[str] = None
    is_current: bool
    created_at: Optional[datetime] = None

    @computed_field
    @property
    def version_number(self) -> str:
        return f"{self.version_major}.{self.version_minor}"

    class Config:
        from_attributes = True


class DocumentSearchResultSchema(BaseModel):
    doc_id: int
    title: str
    type: Optional[str] = None
    status: Optional[str] = None
    author_id: Optional[str] = None
    curator_id: Optional[str] = None
    folder_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    score: float = 0.0


class DocumentSearchResponse(BaseModel):
    total: int
    results: List[DocumentSearchResultSchema]
    error: Optional[str] = None


# Stream & Conversion
class DocumentStreamResponse(BaseModel):
    document_id: int
    file_name: str
    file_size: int
    mime_type: str
    file_type: str


class ConversionRequest(BaseModel):
    document_id: int = Field(..., description="ID документа для конвертации")
    force: bool = Field(default=False, description="Принудительная конвертация даже при наличии кэша")


class ConversionResponse(BaseModel):
    document_id: int
    task_id: Optional[str] = None
    status: str
    converted_path: Optional[str] = None
    error_message: Optional[str] = None
    message: str


class DownloadLogResponse(BaseModel):
    id: int
    document_id: int
    user_id: str
    user_email: Optional[str] = None
    user_username: Optional[str] = None
    downloaded_at: datetime
    file_type: str
    file_size: int
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

    class Config:
        from_attributes = True


class DownloadLogsListResponse(BaseModel):
    total: int
    logs: list[DownloadLogResponse]


class DocumentViewerConfig(BaseModel):
    document_id: int
    file_name: str
    file_type: str
    file_url: str
    total_pages: Optional[int] = None
    file_size: int


# Acknowledgments
class DocumentAcknowledgmentAssignSchema(BaseModel):
    employee_eids: List[str] = Field(
        ...,
        description="Список EID сотрудников, которые должны ознакомиться",
        min_length=1
    )
    required_at: Optional[datetime] = Field(
        None,
        description="Дата/время когда требуется ознакомление (по умолчанию сейчас)"
    )


class DocumentAcknowledgmentSchema(BaseModel):
    id: int = Field(..., description="ID записи ознакомления")
    document_id: int = Field(..., description="ID документа")
    employee_eid: str = Field(..., description="EID сотрудника")
    required_at: datetime = Field(..., description="Дата требования ознакомления")
    acknowledged_at: Optional[datetime] = Field(None, description="Дата фактического ознакомления")
    acknowledged_by: Optional[str] = Field(None, description="EID ознакомившего")
    created_at: datetime = Field(..., description="Дата создания записи")

    class Config:
        from_attributes = True


class DocumentAcknowledgmentDetailSchema(DocumentAcknowledgmentSchema):
    document_name: str = Field(..., description="Название документа")
    is_overdue: bool = Field(False, description="Просрочено ли ознакомление")


class DocumentAcknowledgmentStatusSchema(BaseModel):
    employee_eid: str = Field(..., description="EID сотрудника")
    total_documents: int = Field(..., description="Общее количество документов для ознакомления")
    acknowledged_count: int = Field(..., description="Количество ознакомленных документов")
    pending_count: int = Field(..., description="Количество неознакомленных документов")
    overdue_count: int = Field(..., description="Количество просроченных документов")


class DocumentAcknowledgmentListResponse(BaseModel):
    total: int
    acknowledgments: List[DocumentAcknowledgmentDetailSchema]


class DocumentAcknowledgmentExportSchema(BaseModel):
    id: int
    document_id: int
    document_name: str
    employee_eid: str
    employee_full_name: Optional[str] = None
    required_at: datetime
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]
    status: str
    is_overdue: bool
