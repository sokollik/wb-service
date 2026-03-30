from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.models.notification import (
    NotificationOrm,
    NotificationPreferencesOrm,
    NotificationType,
    UserBotMappingOrm,
)
from core.models.emploee import EmployeeOrm
from core.services.band_bot_client import band_bot_client, BandMessageResponse
from core.repositories.notification_repo import NotificationRepository

class NotificationEventService:
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.notification_repo = NotificationRepository(session)
    
    async def _get_user_preferences(self, user_eid: str) -> NotificationPreferencesOrm:
        prefs = await self.notification_repo.get_preferences(user_eid)
        if not prefs:
            prefs = await self.notification_repo.create_preferences(user_eid)
        return prefs
    
    async def _should_send_notification(
        self,
        user_eid: str,
        notification_type: NotificationType,
    ) -> bool:
        prefs = await self._get_user_preferences(user_eid)
        
        if notification_type in [
            NotificationType.NEWS_PUBLISHED,
            NotificationType.NEWS_UPDATED,
            NotificationType.NEWS_MANDATORY_ACK,
        ]:
            return prefs.receive_news
        
        if notification_type in [
            NotificationType.DOCUMENT_PUBLISHED,
            NotificationType.DOCUMENT_NEW_VERSION,
            NotificationType.DOCUMENT_ACKNOWLEDGMENT_ASSIGNED,
        ]:
            return prefs.receive_documents
        
        if notification_type in [
            NotificationType.BIRTHDAY_TODAY,
            NotificationType.BIRTHDAY_TOMORROW,
        ]:
            return prefs.receive_birthdays
        
        if notification_type in [
            NotificationType.COMMENT_ADDED,
            NotificationType.COMMENT_REPLY,
        ]:
            return prefs.receive_comments
        
        return True
    
    async def _create_notification(
        self,
        user_eid: str,
        event_type: NotificationType,
        title: str,
        message: str,
        payload: dict,
        is_mandatory: bool = False,
    ) -> NotificationOrm:
        notification = await self.notification_repo.create_notification(
            user_eid=user_eid,
            event_type=event_type.value,
            title=title,
            message=message,
            payload=payload,
            is_mandatory=is_mandatory,
        )
        return notification
    
    async def _send_push_notification(
        self,
        user_eid: str,
        title: str,
        message: str,
        buttons: Optional[List] = None,
        payload: Optional[dict] = None,
    ) -> BandMessageResponse:

        mapping = await self.session.execute(
            select(UserBotMappingOrm).where(
                UserBotMappingOrm.user_eid == user_eid,
                UserBotMappingOrm.is_active == True,
            )
        )
        bot_mapping = mapping.scalar_one_or_none()
        
        if not bot_mapping:
            return BandMessageResponse(
                success=False,
                error="User not found in bot mappings",
            )
        
        prefs = await self._get_user_preferences(user_eid)
        if not prefs.channel_messenger:
            return BandMessageResponse(
                success=False,
                error="Messenger notifications disabled",
            )

        response = await band_bot_client.send_message(
            chat_id=bot_mapping.band_chat_id,
            title=title,
            message=message,
            buttons=buttons,
            payload=payload,
        )
        
        if response.success:
            bot_mapping.last_delivery_at = datetime.utcnow()
            bot_mapping.delivery_error_count = 0
            await self.session.flush()
        else:
            bot_mapping.delivery_error_count += 1
            if bot_mapping.delivery_error_count >= 5:
                bot_mapping.is_active = False
            await self.session.flush()
        
        return response
    
    async def notify_document_published(
        self,
        document_id: int,
        document_name: str,
        created_by: str,
        target_users: Optional[List[str]] = None,
    ):

        if target_users is None:
            result = await self.session.execute(
                select(EmployeeOrm.eid).where(EmployeeOrm.is_fired == False)
            )
            target_users = [row[0] for row in result.all()]
        
        for user_eid in target_users:
            if not await self._should_send_notification(
                user_eid, NotificationType.DOCUMENT_PUBLISHED
            ):
                continue

            notification = await self._create_notification(
                user_eid=user_eid,
                event_type=NotificationType.DOCUMENT_PUBLISHED,
                title="📄 Новый документ",
                message=f"Опубликован новый документ: {document_name}",
                payload={
                    "document_id": document_id,
                    "document_name": document_name,
                    "created_by": created_by,
                },
                is_mandatory=False,
            )
            
            buttons = [
                [
                    {"text": "📖 Открыть", "url": f"/documents/{document_id}"},
                ]
            ]
            await self._send_push_notification(
                user_eid=user_eid,
                title="Новый документ",
                message=f"Опубликован: {document_name}",
                buttons=buttons,
                payload={"document_id": document_id},
            )
    
    async def notify_document_new_version(
        self,
        document_id: int,
        document_name: str,
        version_number: int,
        users_to_notify: Optional[List[str]] = None,
    ):

        if users_to_notify is None:
            from core.models.document import DocumentAcknowledgment
            result = await self.session.execute(
                select(DocumentAcknowledgment.employee_eid).where(
                    DocumentAcknowledgment.document_id == document_id
                ).distinct()
            )
            users_to_notify = [row[0] for row in result.all()]
        
        for user_eid in users_to_notify:
            if not await self._should_send_notification(
                user_eid, NotificationType.DOCUMENT_NEW_VERSION
            ):
                continue
            
            notification = await self._create_notification(
                user_eid=user_eid,
                event_type=NotificationType.DOCUMENT_NEW_VERSION,
                title="🔄 Новая версия документа",
                message=f"Документ '{document_name}' обновлён до версии {version_number}",
                payload={
                    "document_id": document_id,
                    "document_name": document_name,
                    "version_number": version_number,
                },
                is_mandatory=False,
            )
            
            buttons = [
                [
                    {"text": "📖 Открыть", "url": f"/documents/{document_id}"},
                ]
            ]
            await self._send_push_notification(
                user_eid=user_eid,
                title="Обновление документа",
                message=f"Версия {version_number}: {document_name}",
                buttons=buttons,
                payload={"document_id": document_id},
            )
    
    async def notify_acknowledgment_assigned(
        self,
        document_id: int,
        document_name: str,
        employee_eid: str,
        required_at: datetime,
        assigned_by: str,
    ):

        if not await self._should_send_notification(
            employee_eid, NotificationType.DOCUMENT_ACKNOWLEDGMENT_ASSIGNED
        ):
            return
        
        notification = await self._create_notification(
            user_eid=employee_eid,
            event_type=NotificationType.DOCUMENT_ACKNOWLEDGMENT_ASSIGNED,
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
        
        response = await band_bot_client.send_document_notification(
            chat_id="",
            document_name=document_name,
            document_id=document_id,
            action="acknowledge",
        )
        
        if response.success:
            notification.sent_at = datetime.utcnow()
            await self.session.flush()
    
    async def notify_news_published(
        self,
        news_id: int,
        news_title: str,
        author_id: str,
        is_mandatory: bool = False,
    ):

        event_type = (
            NotificationType.NEWS_MANDATORY_ACK if is_mandatory
            else NotificationType.NEWS_PUBLISHED
        )
        
        result = await self.session.execute(
            select(EmployeeOrm.eid).where(EmployeeOrm.is_fired == False)
        )
        target_users = [row[0] for row in result.all()]
        
        for user_eid in target_users:
            if not await self._should_send_notification(user_eid, event_type):
                continue
            
            notification = await self._create_notification(
                user_eid=user_eid,
                event_type=event_type,
                title="⚠️ Важное уведомление" if is_mandatory else "📰 Новая новость",
                message=f"Опубликована новость: {news_title}",
                payload={
                    "news_id": news_id,
                    "news_title": news_title,
                    "author_id": author_id,
                    "is_mandatory": is_mandatory,
                },
                is_mandatory=is_mandatory,
            )
            
            response = await band_bot_client.send_news_notification(
                chat_id="",
                news_title=news_title,
                news_id=news_id,
                is_mandatory=is_mandatory,
            )
            
            if response.success:
                notification.sent_at = datetime.utcnow()
                await self.session.flush()
    
    async def notify_status_change_draft_to_active(
        self,
        document_id: int,
        document_name: str,
        old_status: str,
        new_status: str,
    ):
        if old_status != "DRAFT" or new_status != "ACTIVE":
            return
        
        from core.models.document import Document
        doc_result = await self.session.execute(
            select(Document).where(Document.id == document_id)
        )
        document = doc_result.scalar_one_or_none()
        
        if not document:
            return
        
        notification = await self._create_notification(
            user_eid=document.created_by,
            event_type=NotificationType.DOCUMENT_PUBLISHED,
            title="✅ Документ опубликован",
            message=f"Ваш документ '{document_name}' опубликован",
            payload={
                "document_id": document_id,
                "document_name": document_name,
                "old_status": old_status,
                "new_status": new_status,
            },
            is_mandatory=False,
        )
        
        await self.notify_document_published(
            document_id=document_id,
            document_name=document_name,
            created_by=document.created_by,
        )
