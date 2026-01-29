from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class NewsListResponseSchema(BaseModel):
    """Схема для краткого отображения новости в списке"""

    id: int
    title: str
    short_description: str
    author_name: str = Field(..., description="ФИО автора")
    published_at: datetime
    is_pinned: bool

    # Счётчики
    views_count: int
    likes_count: int = 0
    comments_count: int = 0

    class Config:
        from_attributes = True


class NewsFilterSchema(BaseModel):
    """Схема для валидации входных параметров фильтрации и пагинации"""

    category_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: str = "newest"  # newest, popular, discussed
    page: int = Field(1, ge=1)
    size: int = 15


class CategorySchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class CategoryCreateSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)

class NewsFullSchema(NewsListResponseSchema):
    """Расширенная схема новости (например, для детальной страницы)"""

    content: str
    mandatory_ack: bool
    expires_at: Optional[datetime] = None
    tags: List[str] = []
    categories: List[CategorySchema] = []

    class Config:
        from_attributes = True


class NewsDetailSchema(NewsListResponseSchema):
    content: str
    mandatory_ack: bool
    files: List[int] = []

    class Config:
        from_attributes = True


class NewsCreateSchema(BaseModel):
    title: str = Field(..., min_length=5)
    content: str = Field(..., description="Форматированный текст (HTML/Markdown)")
    short_description: str = Field(..., max_length=500)
    category_id: int
    tag_names: List[str] = []  # Список хештегов строками
    is_pinned: bool = False
    mandatory_ack: bool = False
    file_ids: List[int] = []  # Принимаем только список ID файлов


class NewsUpdateSchema(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    short_description: Optional[str] = None
    category_id: Optional[int] = None
    tag_names: Optional[List[str]] = None
    is_pinned: Optional[bool] = None
    mandatory_ack: Optional[bool] = None
    file_ids: Optional[List[int]] = None
