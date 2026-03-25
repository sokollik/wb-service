from datetime import datetime
from typing import List, Optional

from sqlalchemy import delete, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.notification import (
    NotificationOrm,
    NotificationPreferencesOrm,
)


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_notifications(
        self,
        user_eid: str,
        limit: int = 20,
        offset: int = 0,
        is_read: Optional[bool] = None,
        event_type: Optional[str] = None,
    ) -> List[dict]:
        query = select(NotificationOrm).where(
            NotificationOrm.user_eid == user_eid
        )

        if is_read is not None:
            query = query.where(NotificationOrm.is_read == is_read)

        if event_type is not None:
            query = query.where(NotificationOrm.event_type == event_type)

        query = query.order_by(
            desc(NotificationOrm.is_mandatory),
            desc(NotificationOrm.created_at)
        ).limit(limit).offset(offset)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_notification_by_id(
        self, notification_id: int, user_eid: str
    ) -> Optional[NotificationOrm]:
        query = select(NotificationOrm).where(
            NotificationOrm.id == notification_id,
            NotificationOrm.user_eid == user_eid
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_notification(
        self,
        user_eid: str,
        event_type: str,
        title: str,
        message: str,
        payload: Optional[dict] = None,
        is_mandatory: bool = False,
    ) -> NotificationOrm:
        notification = NotificationOrm(
            user_eid=user_eid,
            event_type=event_type,
            title=title,
            message=message,
            payload=payload,
            is_mandatory=is_mandatory,
        )
        self.session.add(notification)
        await self.session.flush()
        return notification

    async def create_notifications_bulk(
        self, notifications_data: List[dict]
    ) -> List[NotificationOrm]:
        notifications = [
            NotificationOrm(**data) for data in notifications_data
        ]
        self.session.add_all(notifications)
        await self.session.flush()
        return notifications

    async def mark_as_read(
        self, notification_id: int, user_eid: str
    ) -> bool:
        result = await self.session.execute(
            update(NotificationOrm)
            .where(
                NotificationOrm.id == notification_id,
                NotificationOrm.user_eid == user_eid
            )
            .values(is_read=True)
        )
        await self.session.commit()
        return result.rowcount > 0

    async def mark_all_as_read(self, user_eid: str) -> int:
        result = await self.session.execute(
            update(NotificationOrm)
            .where(
                NotificationOrm.user_eid == user_eid,
                NotificationOrm.is_read == False
            )
            .values(is_read=True)
        )
        await self.session.commit()
        return result.rowcount

    async def delete_notification(
        self, notification_id: int, user_eid: str
    ) -> bool:
        result = await self.session.execute(
            delete(NotificationOrm).where(
                NotificationOrm.id == notification_id,
                NotificationOrm.user_eid == user_eid
            )
        )
        await self.session.commit()
        return result.rowcount > 0

    async def delete_old_notifications(
        self, older_than: datetime, user_eid: Optional[str] = None
    ) -> int:
        query = delete(NotificationOrm).where(
            NotificationOrm.created_at < older_than
        )
        if user_eid:
            query = query.where(NotificationOrm.user_eid == user_eid)
        
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount

    async def get_unread_count(self, user_eid: str) -> int:
        query = select(func.count(NotificationOrm.id)).where(
            NotificationOrm.user_eid == user_eid,
            NotificationOrm.is_read == False
        )
        result = await self.session.execute(query)
        return result.scalar()

    async def get_preferences(
        self, user_eid: str
    ) -> Optional[NotificationPreferencesOrm]:
        query = select(NotificationPreferencesOrm).where(
            NotificationPreferencesOrm.user_eid == user_eid
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_preferences(
        self,
        user_eid: str,
        channel_portal: bool = True,
        channel_email: bool = True,
        channel_messenger: bool = False,
        digest_daily: bool = False,
    ) -> NotificationPreferencesOrm:
        preferences = NotificationPreferencesOrm(
            user_eid=user_eid,
            channel_portal=channel_portal,
            channel_email=channel_email,
            channel_messenger=channel_messenger,
            digest_daily=digest_daily,
        )
        self.session.add(preferences)
        await self.session.flush()
        return preferences

    async def update_preferences(
        self, user_eid: str, preferences_data: dict
    ) -> Optional[NotificationPreferencesOrm]:
        result = await self.session.execute(
            update(NotificationPreferencesOrm)
            .where(NotificationPreferencesOrm.user_eid == user_eid)
            .values(**preferences_data)
            .returning(NotificationPreferencesOrm)
        )
        await self.session.commit()
        return result.scalar_one_or_none()
