from datetime import datetime, timezone, timedelta
from typing import List, Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete, insert

from core.common.common_exc import NotFoundHttpException, ForbiddenHttpException
from core.models.notification import (
    NotificationOrm,
    NotificationPreferencesOrm,
    UserBotMappingOrm,
)
from core.schemas.notification_schema import (
    NotificationCreateSchema,
    NotificationPreferencesUpdateSchema,
    NotificationSchema,
    NotificationStatsSchema,
    UserBotMappingSchema,
    NotificationTypeSchema,
)
from core.services.band_bot_client import band_bot_client


class NotificationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_notifications(
        self,
        user_eid: str,
        page: int = 1,
        size: int = 20,
        is_read: Optional[bool] = None,
        event_type: Optional[str] = None,
    ) -> dict:
        offset = (page - 1) * size

        # Формируем запрос на выборку уведомлений пользователя
        stmt = select(NotificationOrm).where(NotificationOrm.user_eid == user_eid)
        if is_read is not None:
            stmt = stmt.where(NotificationOrm.is_read == is_read)
        if event_type is not None:
            stmt = stmt.where(NotificationOrm.event_type == event_type)
        
        # Сортировка по умолчанию: сначала новые
        stmt = stmt.order_by(NotificationOrm.created_at.desc()).offset(offset).limit(size)
        
        result = await self.session.execute(stmt)
        notifications = result.scalars().all()

        # Подсчет общего количества непрочитанных
        unread_stmt = select(func.count(NotificationOrm.id)).where(
            NotificationOrm.user_eid == user_eid,
            NotificationOrm.is_read == False
        )
        unread_result = await self.session.execute(unread_stmt)
        unread_count = unread_result.scalar() or 0
        
        notification_dicts = [
            {
                "id": n.id,
                "user_eid": n.user_eid,
                "event_type": n.event_type,
                "title": n.title,
                "message": n.message,
                "payload": n.payload if n.payload else None,
                "is_read": n.is_read,
                "is_mandatory": n.is_mandatory,
                "created_at": n.created_at.isoformat() if n.created_at else None,
                "sent_at": n.sent_at.isoformat() if n.sent_at else None,
                "delivered_at": n.delivered_at.isoformat() if n.delivered_at else None,
            }
            for n in notifications
        ]

        return {
            "total": len(notification_dicts),
            "unread_count": unread_count,
            "notifications": notification_dicts,
            "page": page,
            "size": size,
        }

    async def get_notification_stats(self, user_eid: str) -> NotificationStatsSchema:
        # 1. Всего уведомлений
        total_stmt = select(func.count(NotificationOrm.id)).where(NotificationOrm.user_eid == user_eid)
        total_res = await self.session.execute(total_stmt)
        total_count = total_res.scalar() or 0

        # 2. Непрочитанных уведомлений
        unread_stmt = select(func.count(NotificationOrm.id)).where(
            NotificationOrm.user_eid == user_eid, NotificationOrm.is_read == False
        )
        unread_res = await self.session.execute(unread_stmt)
        unread_count = unread_res.scalar() or 0
        
        read_count = max(0, total_count - unread_count)

        # 3. Обязательные непрочитанные (is_mandatory)
        mandatory_stmt = select(func.count(NotificationOrm.id)).where(
            NotificationOrm.user_eid == user_eid,
            NotificationOrm.is_read == False,
            NotificationOrm.is_mandatory == True,
        )
        mandatory_res = await self.session.execute(mandatory_stmt)
        mandatory_unread = mandatory_res.scalar() or 0

        # 4. Группировка по типам событий
        type_stmt = (
            select(NotificationOrm.event_type, func.count(NotificationOrm.id))
            .where(NotificationOrm.user_eid == user_eid)
            .group_by(NotificationOrm.event_type)
        )
        type_res = await self.session.execute(type_stmt)
        by_type = {row[0]: row[1] for row in type_res.all()}

        return NotificationStatsSchema(
            total_count=total_count,
            unread_count=unread_count,
            read_count=read_count,
            mandatory_unread=mandatory_unread,
            by_type=by_type,
        )

    async def get_notification_by_id(self, notification_id: int, user_eid: str) -> NotificationSchema:
        stmt = select(NotificationOrm).where(
            NotificationOrm.id == notification_id, NotificationOrm.user_eid == user_eid
        )
        res = await self.session.execute(stmt)
        notification = res.scalar_one_or_none()
        
        if not notification:
            raise NotFoundHttpException(name="notification")
        return NotificationSchema.model_validate(notification)

    async def create_notification(self, data: NotificationCreateSchema) -> int:
        notification = NotificationOrm(
            user_eid=data.user_eid,
            event_type=data.event_type,
            title=data.title,
            message=data.message,
            payload=data.payload,
            is_mandatory=data.is_mandatory,
        )
        self.session.add(notification)
        await self.session.commit()
        return notification.id

    async def create_notifications_bulk(self, notifications_data: List[NotificationCreateSchema]) -> List[int]:
        if not notifications_data:
            return []
            
        # Используем оптимизированную множественную вставку через Core insert()
        mappings = [n.model_dump() for n in notifications_data]
        stmt = insert(NotificationOrm).values(mappings).returning(NotificationOrm.id)
        res = await self.session.execute(stmt)
        await self.session.commit()
        return [row[0] for row in res.all()]

    async def mark_as_read(self, notification_id: int, user_eid: str) -> bool:
        stmt = (
            update(NotificationOrm)
            .where(NotificationOrm.id == notification_id, NotificationOrm.user_eid == user_eid)
            .values(is_read=True)
        )
        res = await self.session.execute(stmt)
        await self.session.commit()
        return res.rowcount > 0

    async def mark_all_as_read(self, user_eid: str) -> int:
        stmt = (
            update(NotificationOrm)
            .where(NotificationOrm.user_eid == user_eid, NotificationOrm.is_read == False)
            .values(is_read=True)
        )
        res = await self.session.execute(stmt)
        await self.session.commit()
        return res.rowcount

    async def delete_notification(self, notification_id: int, user_eid: str) -> bool:
        stmt = delete(NotificationOrm).where(
            NotificationOrm.id == notification_id, NotificationOrm.user_eid == user_eid
        )
        res = await self.session.execute(stmt)
        await self.session.commit()
        return res.rowcount > 0

    async def get_preferences(self, user_eid: str) -> NotificationPreferencesOrm:
        stmt = select(NotificationPreferencesOrm).where(NotificationPreferencesOrm.user_eid == user_eid)
        res = await self.session.execute(stmt)
        preferences = res.scalar_one_or_none()
        
        if not preferences:
            preferences = NotificationPreferencesOrm(user_eid=user_eid)
            self.session.add(preferences)
            await self.session.commit()
            
        return preferences

    async def update_preferences(
        self, user_eid: str, data: NotificationPreferencesUpdateSchema
    ) -> NotificationPreferencesOrm:
        # Гарантируем, что запись существует
        await self.get_preferences(user_eid=user_eid)
        
        update_data = data.model_dump(exclude_unset=True)
        stmt = (
            update(NotificationPreferencesOrm)
            .where(NotificationPreferencesOrm.user_eid == user_eid)
            .values(**update_data)
            .returning(NotificationPreferencesOrm)
        )
        res = await self.session.execute(stmt)
        await self.session.commit()
        return res.scalar_one()

    async def cleanup_old_notifications(self, days: int = 30, user_eid: Optional[str] = None) -> int:
        older_than = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = delete(NotificationOrm).where(NotificationOrm.created_at < older_than)
        if user_eid:
            stmt = stmt.where(NotificationOrm.user_eid == user_eid)
            
        res = await self.session.execute(stmt)
        await self.session.commit()
        return res.rowcount
    
    async def link_bot_account(
        self, user_eid: str, band_chat_id: str, band_user_id: Optional[str] = None
    ) -> UserBotMappingSchema:
        stmt = select(UserBotMappingOrm).where(UserBotMappingOrm.user_eid == user_eid)
        res = await self.session.execute(stmt)
        mapping = res.scalar_one_or_none()

        if mapping:
            mapping.band_chat_id = band_chat_id
            mapping.band_user_id = band_user_id
            mapping.is_active = True
        else:
            mapping = UserBotMappingOrm(
                user_eid=user_eid, band_chat_id=band_chat_id, band_user_id=band_user_id
            )
            self.session.add(mapping)
            
        await self.session.commit()
        return UserBotMappingSchema.model_validate(mapping)

    async def get_bot_mapping(self, user_eid: str) -> Optional[UserBotMappingSchema]:
        stmt = select(UserBotMappingOrm).where(UserBotMappingOrm.user_eid == user_eid)
        res = await self.session.execute(stmt)
        mapping = res.scalar_one_or_none()
        return UserBotMappingSchema.model_validate(mapping) if mapping else None

    async def unlink_bot_account(self, user_eid: str) -> bool:
        stmt = select(UserBotMappingOrm).where(UserBotMappingOrm.user_eid == user_eid)
        res = await self.session.execute(stmt)
        mapping = res.scalar_one_or_none()

        if mapping:
            await self.session.delete(mapping)
            await self.session.commit()
            return True
        return False

    async def send_test_notification(self, user_eid: str) -> dict:
        stmt = select(UserBotMappingOrm).where(UserBotMappingOrm.user_eid == user_eid)
        res = await self.session.execute(stmt)
        mapping = res.scalar_one_or_none()
        
        if not mapping:
            raise ForbiddenHttpException(detail="Band Bot аккаунт не привязан.")

        response = await band_bot_client.send_message(
            chat_id=mapping.band_chat_id,
            title="🧪 Тестовое уведомление",
            message="Интеграция работает корректно.",
            buttons=[[{"text": "✅ Всё работает", "url": "/notifications"}]],
        )

        if response.success:
            mapping.last_delivery_at = datetime.now(timezone.utc)
            mapping.delivery_error_count = 0
            await self.session.commit()
            return {"success": True, "message": "Тестовое уведомление отправлено"}
        else:
            mapping.delivery_error_count += 1
            await self.session.commit()
            raise ForbiddenHttpException(detail=f"Ошибка отправки: {response.error}")