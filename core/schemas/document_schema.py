from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

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
    current_version: int
    s3_key: str
    original_filename: str
    file_size: int
    mime_type: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    folder_id: Optional[int] = None
    status: Optional[DocumentStatus] = None
    description: Optional[str] = None
    curator_id: Optional[str] = None
