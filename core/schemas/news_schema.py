from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CategorySchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class CategoryCreateSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)


class NewsListResponseSchema(BaseModel):
    id: int
    title: str
    short_description: str
    author_name: str = Field(...)
    categories: List[CategorySchema] = []
    file_ids: List[int] = []
    published_at: datetime
    is_pinned: bool

    views_count: int
    likes_count: int = 0
    comments_count: int = 0
    is_liked: bool = False

    class Config:
        from_attributes = True


class NewsFullSchema(BaseModel):

    id: int
    title: str
    short_description: str
    author_name: str = Field(...)
    file_ids: List[int] = []
    published_at: datetime
    is_pinned: bool

    views_count: int
    likes_count: int = 0
    comments_count: int = 0
    is_liked: bool = False

    content: str
    mandatory_ack: bool
    expires_at: Optional[datetime] = None
    tags: List[str] = []
    categories: List[CategorySchema] = []

    class Config:
        from_attributes = True


class NewsCreateSchema(BaseModel):
    title: str = Field(..., min_length=5)
    content: str = Field(...)
    short_description: str = Field(..., max_length=500)
    category_ids: List[int]
    tag_names: List[str] = []
    is_pinned: bool = False
    mandatory_ack: bool = False
    file_ids: List[int] = []


class NewsUpdateSchema(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    short_description: Optional[str] = None
    category_ids: Optional[List[int]] = None
    tag_names: Optional[List[str]] = None
    is_pinned: Optional[bool] = None
    mandatory_ack: Optional[bool] = None
    file_ids: Optional[List[int]] = None
