from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from core.models.enums import NewsStatus


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
    comments_enabled: bool = True

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
    comments_enabled: bool = True

    views_count: int
    likes_count: int = 0
    comments_count: int = 0
    is_liked: bool = False

    content: str
    mandatory_ack: bool
    ack_target_all: bool = True
    is_acknowledged: bool = False
    must_acknowledge: bool = False
    expires_at: Optional[datetime] = None
    scheduled_publish_at: Optional[datetime] = None
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
    ack_target_all: bool = True
    ack_target_eids: List[str] = []
    ack_target_org_unit_ids: List[int] = []
    comments_enabled: bool = True
    file_ids: List[int] = []
    status: NewsStatus = NewsStatus.PUBLISHED
    scheduled_publish_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class NewsUpdateSchema(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    short_description: Optional[str] = None
    category_ids: Optional[List[int]] = None
    tag_names: Optional[List[str]] = None
    is_pinned: Optional[bool] = None
    mandatory_ack: Optional[bool] = None
    ack_target_all: Optional[bool] = None
    ack_target_eids: Optional[List[str]] = None
    ack_target_org_unit_ids: Optional[List[int]] = None
    comments_enabled: Optional[bool] = None
    file_ids: Optional[List[int]] = None
    status: Optional[NewsStatus] = None
    scheduled_publish_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class AcknowledgementTargetSchema(BaseModel):
    user_eid: str
    full_name: str
    acknowledged: bool
    acknowledged_at: Optional[datetime] = None


class AcknowledgementStatusSchema(BaseModel):
    news_id: int
    ack_target_all: bool
    total_targets: int
    acknowledged_count: int
    targets: List[AcknowledgementTargetSchema]
