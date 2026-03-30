from datetime import datetime, timedelta
from typing import List, Optional, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.common.common_exc import NotFoundHttpException, ForbiddenHttpException
from core.models.notification import (
    NotificationOrm,
    NotificationPreferencesOrm,
    UserBotMappingOrm,
)
from core.repositories.notification_repo import NotificationRepository
from core.schemas.notification_schema import (
    NotificationCreateSchema,
    NotificationPreferencesUpdateSchema,
    NotificationSchema,
    NotificationStatsSchema,
    UserBotMappingSchema,
)
from core.services.band_bot_client import band_bot_client


class NotificationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.notification_repo = NotificationRepository(session)

    async def get_notifications(
        self,
        user_eid: str,
        page: int = 1,
        size: int = 20,
        is_read: Optional[bool] = None,
        event_type: Optional[str] = None,
    ) -> dict:
        offset = (page - 1) * size

        notifications = await self.notification_repo.get_notifications(
            user_eid=user_eid,
            limit=size,
            offset=offset,
            is_read=is_read,
            event_type=event_type,
        )

        unread_count = await self.notification_repo.get_unread_count(user_eid)

        return {
            "total": unread_count + len([n for n in notifications if n.is_read]),
            "unread_count": unread_count,
            "notifications": [
                NotificationSchema.model_validate(n) for n in notifications
            ],
            "page": page,
            "size": size,
        }

    async def get_notification_stats(
        self,
        user_eid: str,
    ) -> NotificationStatsSchema:
        total_result = await self.session.execute(
            select(func.count(NotificationOrm.id)).where(
                NotificationOrm.user_eid == user_eid
            )
        )
        total_count = total_result.scalar() or 0
        unread_count = await self.notification_repo.get_unread_count(user_eid)

        read_count = total_count - unread_count

        mandatory_result = await self.session.execute(
            select(func.count(NotificationOrm.id)).where(
                NotificationOrm.user_eid == user_eid,
                NotificationOrm.is_read == False,
                NotificationOrm.is_mandatory == True,
            )
        )
        mandatory_unread = mandatory_result.scalar() or 0

        by_type_result = await self.session.execute(
            select(
                NotificationOrm.event_type,
                func.count(NotificationOrm.id),
            )
            .where(NotificationOrm.user_eid == user_eid)
            .group_by(NotificationOrm.event_type)
        )
        by_type = {row[0]: row[1] for row in by_type_result.all()}

        return NotificationStatsSchema(
            total_count=total_count,
            unread_count=unread_count,
            read_count=read_count,
            mandatory_unread=mandatory_unread,
            by_type=by_type,
        )

    async def get_notification_by_id(
        self, notification_id: int, user_eid: str
    ) -> NotificationSchema:
        notification = await self.notification_repo.get_notification_by_id(
            notification_id=notification_id,
            user_eid=user_eid,
        )
        if not notification:
            raise NotFoundHttpException(name="notification")
        return NotificationSchema.model_validate(notification)

    async def create_notification(
        self, data: NotificationCreateSchema
    ) -> int:
        notification = await self.notification_repo.create_notification(
            user_eid=data.user_eid,
            event_type=data.event_type,
            title=data.title,
            message=data.message,
            payload=data.payload,
            is_mandatory=data.is_mandatory,
        )
        await self.session.commit()
        return notification.id

    async def create_notifications_bulk(
        self, notifications_data: List[NotificationCreateSchema]
    ) -> List[int]:
        notifications = await self.notification_repo.create_notifications_bulk(
            notifications_data=[
                {
                    "user_eid": n.user_eid,
                    "event_type": n.event_type,
                    "title": n.title,
                    "message": n.message,
                    "payload": n.payload,
                    "is_mandatory": n.is_mandatory,
                }
                for n in notifications_data
            ]
        )
        await self.session.commit()
        return [n.id for n in notifications]

    async def mark_as_read(
        self, notification_id: int, user_eid: str
    ) -> bool:
        notification = await self.notification_repo.get_notification_by_id(
            notification_id=notification_id,
            user_eid=user_eid,
        )
        if not notification:
            raise NotFoundHttpException(name="notification")

        result = await self.notification_repo.mark_as_read(
            notification_id=notification_id,
            user_eid=user_eid,
        )
        return result

    async def mark_all_as_read(self, user_eid: str) -> int:
        return await self.notification_repo.mark_all_as_read(user_eid=user_eid)

    async def delete_notification(
        self, notification_id: int, user_eid: str
    ) -> bool:
        notification = await self.notification_repo.get_notification_by_id(
            notification_id=notification_id,
            user_eid=user_eid,
        )
        if not notification:
            raise NotFoundHttpException(name="notification")

        return await self.notification_repo.delete_notification(
            notification_id=notification_id,
            user_eid=user_eid,
        )

    async def get_unread_count(self, user_eid: str) -> int:
        return await self.notification_repo.get_unread_count(user_eid=user_eid)

    async def get_preferences(
        self, user_eid: str
    ) -> NotificationPreferencesOrm:
        preferences = await self.notification_repo.get_preferences(
            user_eid=user_eid
        )
        if not preferences:
            preferences = await self.notification_repo.create_preferences(
                user_eid=user_eid
            )
        return preferences

    async def update_preferences(
        self, user_eid: str, data: NotificationPreferencesUpdateSchema
    ) -> NotificationPreferencesOrm:
        update_data = data.model_dump(exclude_unset=True)

        preferences = await self.notification_repo.get_preferences(
            user_eid=user_eid
        )
        if not preferences:
            preferences = await self.notification_repo.create_preferences(
                user_eid=user_eid
            )

        updated = await self.notification_repo.update_preferences(
            user_eid=user_eid,
            preferences_data=update_data,
        )
        return updated

    async def cleanup_old_notifications(
        self, days: int = 30, user_eid: Optional[str] = None
    ) -> int:
        older_than = datetime.utcnow() - timedelta(days=days)
        return await self.notification_repo.delete_old_notifications(
            older_than=older_than,
            user_eid=user_eid,
        )
    
    async def link_bot_account(
        self,
        user_eid: str,
        band_chat_id: str,
        band_user_id: Optional[str] = None,
    ) -> UserBotMappingSchema:

        existing = await self.session.execute(
            select(UserBotMappingOrm).where(
                UserBotMappingOrm.user_eid == user_eid
            )
        )
        existing_mapping = existing.scalar_one_or_none()

        if existing_mapping:
            existing_mapping.band_chat_id = band_chat_id
            existing_mapping.band_user_id = band_user_id
            existing_mapping.is_active = True
            await self.session.flush()
            return UserBotMappingSchema.model_validate(existing_mapping)

        new_mapping = UserBotMappingOrm(
            user_eid=user_eid,
            band_chat_id=band_chat_id,
            band_user_id=band_user_id,
        )
        self.session.add(new_mapping)
        await self.session.flush()
        return UserBotMappingSchema.model_validate(new_mapping)

    async def get_bot_mapping(
        self,
        user_eid: str,
    ) -> Optional[UserBotMappingSchema]:
        result = await self.session.execute(
            select(UserBotMappingOrm).where(
                UserBotMappingOrm.user_eid == user_eid
            )
        )
        mapping = result.scalar_one_or_none()
        if mapping:
            return UserBotMappingSchema.model_validate(mapping)
        return None

    async def unlink_bot_account(
        self,
        user_eid: str,
    ) -> bool:
        result = await self.session.execute(
            select(UserBotMappingOrm).where(
                UserBotMappingOrm.user_eid == user_eid
            )
        )
        mapping = result.scalar_one_or_none()

        if mapping:
            await self.session.delete(mapping)
            await self.session.flush()
            return True
        return False

    async def send_test_notification(
        self,
        user_eid: str,
    ) -> dict:
        mapping = await self.get_bot_mapping(user_eid)
        if not mapping:
            raise ForbiddenHttpException(
                detail="Band Bot аккаунт не привязан. Сначала привяжите аккаунт."
            )

        response = await band_bot_client.send_message(
            chat_id=mapping.band_chat_id,
            title="🧪 Тестовое уведомление",
            message="Это тестовое уведомление от wb-service. Если вы видите это сообщение, значит интеграция работает корректно.",
            buttons=[
                [
                    {"text": "✅ Всё работает", "url": "/notifications"},
                ]
            ],
        )

        if response.success:

            mapping.last_delivery_at = datetime.utcnow()
            mapping.delivery_error_count = 0
            await self.session.flush()

            return {"success": True, "message": "Тестовое уведомление отправлено"}
        else:
            mapping.delivery_error_count += 1
            await self.session.flush()

            raise ForbiddenHttpException(
                detail=f"Ошибка отправки: {response.error}"
            )

    async def send_news_notification(
        self,
        user_eid: str,
        news_title: str,
        news_id: int,
        is_mandatory: bool = False,
    ) -> int:
        notification = await self.notification_repo.create_notification(
            user_eid=user_eid,
            event_type="news_published",
            title="Новая новость",
            message=f"Опубликована новость: {news_title}",
            payload={"news_id": news_id, "news_title": news_title},
            is_mandatory=is_mandatory,
        )
        await self.session.commit()
        return notification.id

    async def send_birthday_notification(
        self,
        user_eid: str,
        birthday_person_eid: str,
        birthday_person_name: str,
    ) -> int:
        notification = await self.notification_repo.create_notification(
            user_eid=user_eid,
            event_type="birthday",
            title="День рождения коллеги",
            message=f"У {birthday_person_name} сегодня день рождения!",
            payload={
                "birthday_person_eid": birthday_person_eid,
                "birthday_person_name": birthday_person_name,
            },
            is_mandatory=False,
        )
        await self.session.commit()
        return notification.id
