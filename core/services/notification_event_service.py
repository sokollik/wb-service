import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert

from core.models.notification import (
    NotificationOrm,
    NotificationPreferencesOrm,
    UserBotMappingOrm,
)
from core.models.emploee import EmployeeOrm
from core.schemas.notification_schema import NotificationTypeSchema
from core.services.band_bot_client import band_bot_client


class NotificationEventService:
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def _filter_users_by_preferences(
        self, user_eids: List[str], notification_type: NotificationTypeSchema
    ) -> List[str]:
        if not user_eids:
            return []

        stmt = select(NotificationPreferencesOrm).where(NotificationPreferencesOrm.user_eid.in_(user_eids))
        res = await self.session.execute(stmt)
        prefs_map = {p.user_eid: p for p in res.scalars().all()}
        
        allowed_users = []
        for eid in user_eids:
            prefs = prefs_map.get(eid)
            if not prefs:
                allowed_users.append(eid)
                continue
                
            if notification_type in (NotificationTypeSchema.NEWS_PUBLISHED, NotificationTypeSchema.NEWS_UPDATED, NotificationTypeSchema.NEWS_MANDATORY_ACK):
                if prefs.receive_news: allowed_users.append(eid)
            elif notification_type in (NotificationTypeSchema.DOCUMENT_PUBLISHED, NotificationTypeSchema.DOCUMENT_NEW_VERSION, NotificationTypeSchema.DOCUMENT_ACKNOWLEDGMENT_ASSIGNED):
                if prefs.receive_documents: allowed_users.append(eid)
            elif notification_type in (NotificationTypeSchema.BIRTHDAY_TODAY, NotificationTypeSchema.BIRTHDAY_TOMORROW):
                if prefs.receive_birthdays: allowed_users.append(eid)
            elif notification_type in (NotificationTypeSchema.COMMENT_ADDED, NotificationTypeSchema.COMMENT_REPLY):
                if prefs.receive_comments: allowed_users.append(eid)
            else:
                allowed_users.append(eid)
                
        return allowed_users

    async def _bulk_send_push_notifications(
        self,
        user_eids: List[str],
        title: str,
        message: str,
        buttons: Optional[List] = None,
        payload: Optional[dict] = None,
    ):
        if not user_eids:
            return

        mappings_stmt = select(UserBotMappingOrm).where(
            UserBotMappingOrm.user_eid.in_(user_eids),
            UserBotMappingOrm.is_active == True
        )
        mappings_res = await self.session.execute(mappings_stmt)
        bot_mappings = {m.user_eid: m for m in mappings_res.scalars().all()}
        
        prefs_stmt = select(NotificationPreferencesOrm).where(NotificationPreferencesOrm.user_eid.in_(user_eids))
        prefs_res = await self.session.execute(prefs_stmt)
        prefs_map = {p.user_eid: p for p in prefs_res.scalars().all()}

        semaphore = asyncio.Semaphore(20)

        async def sem_send_message(mapping):
            async with semaphore:
                return await band_bot_client.send_message(
                    chat_id=mapping.band_chat_id,
                    title=title,
                    message=message,
                    buttons=buttons,
                    payload=payload,
                )

        tasks = []
        targeted_mappings = []

        for eid in user_eids:
            mapping = bot_mappings.get(eid)
            prefs = prefs_map.get(eid)
            
            if not mapping or (prefs and not prefs.channel_messenger):
                continue
                
            targeted_mappings.append(mapping)
            tasks.append(sem_send_message(mapping))

        if not tasks:
            return

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for mapping, response in zip(targeted_mappings, responses):
            if isinstance(response, Exception) or not response.success:
                mapping.delivery_error_count += 1
                if mapping.delivery_error_count >= 5:
                    mapping.is_active = False
            else:
                mapping.last_delivery_at = datetime.now(timezone.utc)
                mapping.delivery_error_count = 0

        await self.session.flush()

    async def notify_document_published(
        self, document_id: int, document_name: str, created_by: str, target_users: Optional[List[str]] = None
    ):
        if target_users is None:
            res = await self.session.execute(select(EmployeeOrm.eid).where(EmployeeOrm.is_fired == False))
            target_users = [row[0] for row in res.all()]

        filtered_users = await self._filter_users_by_preferences(target_users, NotificationTypeSchema.DOCUMENT_PUBLISHED)
        if not filtered_users:
            return

        notifications = [
            {
                "user_eid": user_eid,
                "event_type": NotificationTypeSchema.DOCUMENT_PUBLISHED.value,
                "title": "📄 Новый документ",
                "message": f"Опубликован новый документ: {document_name}",
                "payload": {"document_id": document_id, "document_name": document_name, "created_by": created_by},
                "is_mandatory": False,
            }
            for user_eid in filtered_users
        ]
        await self.session.execute(insert(NotificationOrm).values(notifications))

        await self._bulk_send_push_notifications(
            user_eids=filtered_users,
            title="Новый документ",
            message=f"Опубликован: {document_name}",
            buttons=[[{"text": "📖 Открыть", "url": f"/documents/{document_id}"}]],
            payload={"document_id": document_id},
        )
        await self.session.commit()

    async def notify_document_new_version(
        self, document_id: int, document_name: str, version_number: int, users_to_notify: Optional[List[str]] = None
    ):
        if users_to_notify is None:
            from core.models.document import DocumentAcknowledgment
            res = await self.session.execute(
                select(DocumentAcknowledgment.employee_eid).where(
                    DocumentAcknowledgment.document_id == document_id
                ).distinct()
            )
            users_to_notify = [row[0] for row in res.all()]

        filtered_users = await self._filter_users_by_preferences(users_to_notify, NotificationTypeSchema.DOCUMENT_NEW_VERSION)
        if not filtered_users:
            return

        notifications = [
            {
                "user_eid": user_eid,
                "event_type": NotificationTypeSchema.DOCUMENT_NEW_VERSION.value,
                "title": "🔄 Новая версия документа",
                "message": f"Документ '{document_name}' обновлён до версии {version_number}",
                "payload": {"document_id": document_id, "document_name": document_name, "version_number": version_number},
                "is_mandatory": False,
            }
            for user_eid in filtered_users
        ]
        await self.session.execute(insert(NotificationOrm).values(notifications))

        await self._bulk_send_push_notifications(
            user_eids=filtered_users,
            title="Обновление документа",
            message=f"Версия {version_number}: {document_name}",
            buttons=[[{"text": "📖 Открыть", "url": f"/documents/{document_id}"}]],
            payload={"document_id": document_id},
        )
        await self.session.commit()

    async def notify_acknowledgment_assigned(
        self, document_id: int, document_name: str, employee_eid: str, required_at: datetime, assigned_by: str
    ):
        allowed = await self._filter_users_by_preferences([employee_eid], NotificationTypeSchema.DOCUMENT_ACKNOWLEDGMENT_ASSIGNED)
        if not allowed:
            return

        notification = NotificationOrm(
            user_eid=employee_eid,
            event_type=NotificationTypeSchema.DOCUMENT_ACKNOWLEDGMENT_ASSIGNED.value,
            title="📋 Требуется ознакомление",
            message=f"Вам назначено ознакомление с документом '{document_name}' до {required_at.strftime('%d.%m.%Y')}",
            payload={
                "document_id": document_id,
                "document_name": document_name,
                "required_at": required_at.isoformat(),
                "assigned_by": assigned_by,
            },
            is_mandatory=True,
        )
        self.session.add(notification)
        await self.session.flush()

        response = await band_bot_client.send_document_notification(
            chat_id="", document_name=document_name, document_id=document_id, action="acknowledge"
        )
        if response.success:
            notification.sent_at = datetime.now(timezone.utc)

        await self.session.commit()

    async def notify_status_change_draft_to_active(
        self, document_id: int, document_name: str, old_status: str, new_status: str
    ):
        if old_status != "DRAFT" or new_status != "ACTIVE":
            return

        from core.models.document import Document
        doc_res = await self.session.execute(select(Document).where(Document.id == document_id))
        document = doc_res.scalar_one_or_none()

        if not document:
            return

        notification = NotificationOrm(
            user_eid=document.created_by,
            event_type=NotificationTypeSchema.DOCUMENT_PUBLISHED.value,
            title="✅ Документ опубликован",
            message=f"Ваш документ '{document_name}' опубликован",
            payload={"document_id": document_id, "document_name": document_name, "old_status": old_status, "new_status": new_status},
            is_mandatory=False,
        )
        self.session.add(notification)
        await self.session.flush()

        await self.notify_document_published(
            document_id=document_id, document_name=document_name, created_by=document.created_by
        )

    # ВСТАВЛЕНО СЮДА (Заменило старый метод):
    async def notify_news_published(self, news_id: int, news_title: str, author_id: str, is_mandatory: bool = False):
        event_type = NotificationTypeSchema.NEWS_MANDATORY_ACK if is_mandatory else NotificationTypeSchema.NEWS_PUBLISHED

        res = await self.session.execute(select(EmployeeOrm.eid).where(EmployeeOrm.is_fired == False))
        target_users = [row[0] for row in res.all()]

        filtered_users = await self._filter_users_by_preferences(target_users, event_type)
        if not filtered_users:
            return

        # 1. Записываем уведомления в БД пачкой
        notifications = [
            {
                "user_eid": user_eid,
                "event_type": event_type.value,
                "title": "⚠️ Важное уведомление" if is_mandatory else "📰 Новая новость",
                "message": f"Опубликована новость: {news_title}",
                "payload": {"news_id": news_id, "news_title": news_title, "author_id": author_id, "is_mandatory": is_mandatory},
                "is_mandatory": is_mandatory,
            }
            for user_eid in filtered_users
        ]
        await self.session.execute(insert(NotificationOrm).values(notifications))

        # 2. Вызываем наш новый метод с семафором для безопасной отправки пушей
        await self._bulk_send_push_notifications(
            user_eids=filtered_users,
            title="Важное уведомление" if is_mandatory else "Новая новость",
            message=f"Опубликована новость: {news_title}",
            buttons=[[{"text": "Читать новости", "url": f"/news/{news_id}"}]],
        )
        
        # 3. Закрываем транзакцию
        await self.session.commit()