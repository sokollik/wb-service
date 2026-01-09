import sqlalchemy as sa
from sqlalchemy import (
    Boolean,
    Column,
    String,
    func,
    ForeignKey,
    DateTime
)
from sqlalchemy.dialects.postgresql import JSONB
from core.models.base import Base


class NotificationOrm(Base):
    __tablename__ = "notifications"

    id = Column(
        sa.BigInteger,
        primary_key=True,
    )
    user_eid = Column(
        sa.BigInteger,
        ForeignKey("employee.eid", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    event_type = Column(
        String,
        nullable=False,
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
    )
    is_read = Column(
        Boolean,
        default=False,
    )
    is_mandatory = Column(
        Boolean,
        default=False,
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )


class NotificationPreferencesOrm(Base):
    __tablename__ = "notification_preferences"
    
    id = Column(
        sa.BigInteger,
        primary_key=True,
    )
    user_eid = Column(
        sa.BigInteger,
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
    )
    digest_daily = Column(
        Boolean,
        nullable=False,
        default=False,
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )