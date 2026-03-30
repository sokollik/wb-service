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
