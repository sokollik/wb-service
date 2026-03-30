import sqlalchemy as sa
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, func, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from core.models.base import Base

class NotificationType(str, PyEnum):
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


class NotificationOrm(Base):
    __tablename__ = "notifications"

    id = Column(
        sa.BigInteger,
        primary_key=True,
    )
    user_eid = Column(
        String,
        ForeignKey("employee.eid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type = Column(
        String,
        nullable=False,
        index=True,
        comment="Тип события (NEWS_PUBLISHED, DOCUMENT_ACKNOWLEDGMENT_ASSIGNED, etc.)",
    )
    title = Column(
        String,
        nullable=False,
    )
    message = Column(
        String,
        nullable=False,
    )
    payload = Column(
        JSONB,
        nullable=True,
        comment="Дополнительные данные (document_id, news_id, acknowledgment_id, etc.)",
    )
    is_read = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Флаг прочтения",
    )
    is_mandatory = Column(
        Boolean,
        default=False,
        comment="Обязательное уведомление (требует действия)",
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    sent_at = Column(
        DateTime,
        nullable=True,
        comment="Время отправки push-уведомления",
    )
    delivered_at = Column(
        DateTime,
        nullable=True,
        comment="Время доставки push-уведомления",
    )

    __table_args__ = (
        Index("ix_notifications_user_type_read", "user_eid", "event_type", "is_read"),
        Index("ix_notifications_created_is_read", "created_at", "is_read"),
    )


class UserBotMappingOrm(Base):
    __tablename__ = "user_bot_mappings"

    id = Column(
        sa.BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    user_eid = Column(
        String,
        ForeignKey("employee.eid", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="EID пользователя",
    )
    band_chat_id = Column(
        String,
        nullable=False,
        comment="Chat ID в Band Bot для отправки уведомлений",
    )
    band_user_id = Column(
        String,
        nullable=True,
        comment="User ID в Band",
    )
    is_active = Column(
        Boolean,
        default=True,
        comment="Активен ли маппинг",
    )
    last_delivery_at = Column(
        DateTime,
        nullable=True,
        comment="Время последней успешной доставки",
    )
    delivery_error_count = Column(
        sa.Integer,
        default=0,
        comment="Количество последовательных ошибок доставки",
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index("ix_bot_mappings_chat_id", "band_chat_id"),
        Index("ix_bot_mappings_active", "is_active"),
    )


class NotificationPreferencesOrm(Base):
    __tablename__ = "notification_preferences"

    id = Column(
        sa.BigInteger,
        primary_key=True,
    )
    user_eid = Column(
        String,
        ForeignKey("employee.eid", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    channel_portal = Column(
        Boolean,
        nullable=False,
        default=True,
    )
    channel_email = Column(
        Boolean,
        nullable=False,
        default=True,
    )
    channel_messenger = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Отправлять ли уведомления в Band Bot",
    )
    digest_daily = Column(
        Boolean,
        nullable=False,
        default=False,
    )
    receive_news = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Получать уведомления о новостях",
    )
    receive_documents = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Получать уведомления о документах",
    )
    receive_birthdays = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Получать уведомления о днях рождения",
    )
    receive_comments = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Получать уведомления о комментариях",
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )