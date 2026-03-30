from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class NotificationTypeSchema(str, Enum):
    NEWS_PUBLISHED = "NEWS_PUBLISHED"
    NEWS_UPDATED = "NEWS_UPDATED"
    NEWS_MANDATORY_ACK = "NEWS_MANDATORY_ACK"
    
    DOCUMENT_PUBLISHED = "DOCUMENT_PUBLISHED"
    DOCUMENT_NEW_VERSION = "DOCUMENT_NEW_VERSION"
    DOCUMENT_ACKNOWLEDGMENT_ASSIGNED = "DOCUMENT_ACKNOWLEDGMENT_ASSIGNED"
    DOCUMENT_ACKNOWLEDGMENT_OVERDUE = "DOCUMENT_ACKNOWLEDGMENT_OVERDUE"
    
    COMMENT_ADDED = "COMMENT_ADDED"
    COMMENT_REPLY = "COMMENT_REPLY"
    
    BIRTHDAY_TOMORROW = "BIRTHDAY_TOMORROW"
    BIRTHDAY_TODAY = "BIRTHDAY_TODAY"
    
    SYSTEM_MAINTENANCE = "SYSTEM_MAINTENANCE"
    SECURITY_ALERT = "SECURITY_ALERT"


class NotificationPreferencesSchema(BaseModel):
    id: int
    user_eid: str
    channel_portal: bool = True
    channel_email: bool = True
    channel_messenger: bool = False
    digest_daily: bool = False
    receive_news: bool = True
    receive_documents: bool = True
    receive_birthdays: bool = True
    receive_comments: bool = True
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationPreferencesUpdateSchema(BaseModel):
    channel_portal: Optional[bool] = None
    channel_email: Optional[bool] = None
    channel_messenger: Optional[bool] = None
    digest_daily: Optional[bool] = None
    receive_news: Optional[bool] = None
    receive_documents: Optional[bool] = None
    receive_birthdays: Optional[bool] = None
    receive_comments: Optional[bool] = None


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
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationCreateSchema(BaseModel):
    user_eid: str = Field(..., description="EID пользователя")
    event_type: str = Field(..., description="Тип события")
    title: str = Field(..., min_length=1, max_length=200, description="Заголовок уведомления")
    message: str = Field(..., min_length=1, max_length=1000, description="Текст уведомления")
    payload: Optional[Dict[str, Any]] = None
    is_mandatory: bool = False


class NotificationBulkCreateSchema(BaseModel):
    notifications: List[NotificationCreateSchema] = Field(..., min_length=1)


class NotificationListResponseSchema(BaseModel):
    total: int
    unread_count: int
    notifications: List[NotificationSchema]
    page: int
    size: int


class UserBotMappingSchema(BaseModel):
    id: int
    user_eid: str
    band_chat_id: str
    band_user_id: Optional[str] = None
    is_active: bool = True
    last_delivery_at: Optional[datetime] = None
    delivery_error_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class UserBotMappingCreateSchema(BaseModel):
    band_chat_id: str = Field(..., description="Chat ID в Band Bot")
    band_user_id: Optional[str] = Field(None, description="User ID в Band")


class UserBotMappingLinkSchema(BaseModel):
    link_code: str = Field(..., description="Код для привязки")


class NotificationStatsSchema(BaseModel):
    total_count: int = 0
    unread_count: int = 0
    read_count: int = 0
    mandatory_unread: int = 0
    by_type: Dict[str, int] = Field(default_factory=dict)
