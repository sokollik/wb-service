from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class FolderCreateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    parent_id: Optional[int] = None


class FolderUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    parent_id: Optional[int] = None


class FolderSchema(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None
    path: str
    created_by: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FolderTreeSchema(BaseModel):
    id: int
    name: str
    path: str
    children: List["FolderTreeSchema"] = []

    class Config:
        from_attributes = True
