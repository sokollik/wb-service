from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class AuthorSchema(BaseModel):
    eid: int = Field(...)
    full_name: str = Field(...)


class CommentSchema(BaseModel):
    id: int = Field(...)
    parent_id: int | None = Field(None)
    content: str = Field(...)
    author: AuthorSchema = Field(...)
    created_at: datetime = Field(...)
    is_edited: bool = Field(...)
    file_ids: List[int] | None = Field(None)

    likes_count: int = Field(...)
    replies_count: int = Field(...)

    replies: List["CommentSchema"] = Field([])


CommentSchema.model_rebuild()


class CommentViewSchema(BaseModel):
    result: List[CommentSchema] = Field(...)
    count: int = Field(...)


class CommentCreateSchema(BaseModel):
    author_id: int = Field(..., description="EID автора комментария")
    news_id: int = Field(..., description="ID новости")
    parent_id: int | None = Field(
        None, description="ID родительского комментария"
    )
    content: str = Field(..., description="Содержимое комментария")
    file_ids: List[int] | None = Field(
        None, description="Список ID файлов, прикрепленных к комментарию"
    )


class CommentUpdateSchema(BaseModel):
    id: int = Field(..., description="ID комментария для редактирования")
    content: str = Field(..., description="Содержимое комментария")
    file_ids: List[int] | None = Field(
        None, description="Список ID файлов, прикрепленных к комментарию"
    )
