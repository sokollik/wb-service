from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NotificationPreferencesSchema(BaseModel):
    id: int
    user_eid: str
    channel_portal: bool = True
    channel_email: bool = True
    channel_messenger: bool = False
    digest_daily: bool = False
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationPreferencesUpdateSchema(BaseModel):
    channel_portal: Optional[bool] = None
    channel_email: Optional[bool] = None
    channel_messenger: Optional[bool] = None
    digest_daily: Optional[bool] = None


class NotificationSchema(BaseModel):
    id: int
    user_eid: str
    event_type: str
    title: str
    message: str
    payload: Optional[Dict[str, Any]] = None
    is_read: bool = False
    is_mandatory: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationCreateSchema(BaseModel):
    user_eid: str = Field(..., description="EID пользователя")
    event_type: str = Field(..., description="Тип события")
    title: str = Field(..., min_length=1, max_length=200, description="Заголовок уведомления")
    message: str = Field(..., min_length=1, max_length=1000, description="Текст уведомления")
    payload: Optional[Dict[str, Any]] = None
    is_mandatory: bool = False


class NotificationListResponseSchema(BaseModel):
    total: int
    unread_count: int
    notifications: List[NotificationSchema]
    page: int
    size: int


class NotificationBulkCreateSchema(BaseModel):
    notifications: List[NotificationCreateSchema] = Field(..., min_length=1)
