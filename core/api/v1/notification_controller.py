from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from fastapi_restful.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession
from core.api.deps import CurrentUser, require_roles
from core.schemas.notification_schema import (
    NotificationBulkCreateSchema,
    NotificationCreateSchema,
    NotificationListResponseSchema,
    NotificationPreferencesSchema,
    NotificationPreferencesUpdateSchema,
    NotificationSchema,
)
from core.services.notification_service import NotificationService
from core.utils.common_util import exception_handler
from core.utils.db_util import get_session_obj

notification_router = APIRouter(tags=["Notifications"])


@cbv(notification_router)
class NotificationController:
    def __init__(self, session: AsyncSession = Depends(get_session_obj)):
        self.session = session
        self.notification_service = NotificationService(session=session)

    @notification_router.get(
        "/",
        response_model=NotificationListResponseSchema,
        summary="Получить список уведомлений",
        description="Получение списка уведомлений текущего пользователя с поддержкой пагинации и фильтрации",
    )
    @exception_handler
    async def get_notifications(
        self,
        current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
        page: int = Query(1, ge=1, description="Номер страницы"),
        size: int = Query(20, ge=1, le=100, description="Размер страницы"),
        is_read: Optional[bool] = Query(
            None, description="Фильтр по статусу прочтения"
        ),
        event_type: Optional[str] = Query(
            None, description="Фильтр по типу события"
        ),
    ):
        return await self.notification_service.get_notifications(
            user_eid=current_user.eid,
            page=page,
            size=size,
            is_read=is_read,
            event_type=event_type,
        )

    @notification_router.get(
        "/unread-count",
        response_model=int,
        summary="Получить количество непрочитанных уведомлений",
        description="Возвращает количество непрочитанных уведомлений пользователя",
    )
    @exception_handler
    async def get_unread_count(
        self,
        current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
    ):
        return await self.notification_service.get_unread_count(
            user_eid=current_user.eid
        )

    @notification_router.get(
        "/{notification_id}",
        response_model=NotificationSchema,
        summary="Получить уведомление по ID",
        description="Получение конкретного уведомления по его идентификатору",
    )
    @exception_handler
    async def get_notification_by_id(
        self,
        notification_id: int,
        current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
    ):
        return await self.notification_service.get_notification_by_id(
            notification_id=notification_id,
            user_eid=current_user.eid,
        )

    @notification_router.post(
        "/{notification_id}/read",
        summary="Отметить уведомление как прочитанное",
        description="Отметка конкретного уведомления как прочитанного",
    )
    @exception_handler
    async def mark_as_read(
        self,
        notification_id: int,
        current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
    ):
        return await self.notification_service.mark_as_read(
            notification_id=notification_id,
            user_eid=current_user.eid,
        )

    @notification_router.post(
        "/read-all",
        summary="Отметить все уведомления как прочитанные",
        description="Отметка всех уведомлений пользователя как прочитанных",
    )
    @exception_handler
    async def mark_all_as_read(
        self,
        current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
    ):
        return await self.notification_service.mark_all_as_read(
            user_eid=current_user.eid
        )

    @notification_router.delete(
        "/{notification_id}",
        summary="Удалить уведомление",
        description="Удаление конкретного уведомления по его идентификатору",
    )
    @exception_handler
    async def delete_notification(
        self,
        notification_id: int,
        current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
    ):
        return await self.notification_service.delete_notification(
            notification_id=notification_id,
            user_eid=current_user.eid,
        )

    @notification_router.get(
        "/preferences",
        response_model=NotificationPreferencesSchema,
        summary="Получить настройки уведомлений",
        description="Получение текущих настроек уведомлений пользователя",
    )
    @exception_handler
    async def get_preferences(
        self,
        current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
    ):
        return await self.notification_service.get_preferences(
            user_eid=current_user.eid
        )

    @notification_router.patch(
        "/preferences",
        response_model=NotificationPreferencesSchema,
        summary="Обновить настройки уведомлений",
        description="Обновление настроек уведомлений пользователя",
    )
    @exception_handler
    async def update_preferences(
        self,
        data: NotificationPreferencesUpdateSchema,
        current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
    ):
        return await self.notification_service.update_preferences(
            user_eid=current_user.eid,
            data=data,
        )

    @notification_router.post(
        "/",
        response_model=int,
        summary="Создать уведомление",
        description="Создание нового уведомления (доступно только администраторам и редакторам новостей)",
    )
    @exception_handler
    async def create_notification(
        self,
        data: NotificationCreateSchema,
        current_user: CurrentUser = Depends(
            require_roles(["admin", "news_editor"])
        ),
    ):
        return await self.notification_service.create_notification(data=data)

    @notification_router.post(
        "/bulk",
        response_model=List[int],
        summary="Массовое создание уведомлений",
        description="Создание нескольких уведомлений за один запрос (доступно только администраторам)",
    )
    @exception_handler
    async def create_notifications_bulk(
        self,
        data: NotificationBulkCreateSchema,
        current_user: CurrentUser = Depends(require_roles(["admin"])),
    ):
        return await self.notification_service.create_notifications_bulk(
            notifications_data=data.notifications
        )

    @notification_router.delete(
        "/cleanup",
        summary="Очистить старые уведомления",
        description="Удаление уведомлений старше указанного количества дней (доступно только администраторам)",
    )
    @exception_handler
    async def cleanup_old_notifications(
        self,
        days: int = Query(30, ge=1, description="Количество дней"),
        current_user: CurrentUser = Depends(require_roles(["admin"])),
    ):
        return await self.notification_service.cleanup_old_notifications(
            days=days
        )
