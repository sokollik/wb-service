from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi_restful.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession

from core.api.deps import CurrentUser, require_roles, CheckPermissionDep
from core.schemas.notification_schema import (
    NotificationBulkCreateSchema,
    NotificationCreateSchema,
    NotificationListResponseSchema,
    NotificationPreferencesSchema,
    NotificationPreferencesUpdateSchema,
    NotificationSchema,
    NotificationStatsSchema,
    UserBotMappingCreateSchema,
    UserBotMappingSchema,
)
from core.services.notification_service import NotificationService
from core.utils.common_util import exception_handler
from core.utils.db_util import get_session_obj

notification_router = APIRouter(prefix="/notifications", tags=["Notifications"])


@cbv(notification_router)
class NotificationController:
    def __init__(self, session: AsyncSession = Depends(get_session_obj)):
        self.session = session
        self.notification_service = NotificationService(session=session)

    @notification_router.get(
        "/",
        response_model=dict,
    )
    @exception_handler
    async def get_notifications(
        self,
        current_user: CurrentUser = Depends(CheckPermissionDep("notifications", "read")),
        page: int = Query(1, ge=1, description="Номер страницы"),
        size: int = Query(20, ge=1, le=100, description="Размер страницы"),
        is_read: Optional[bool] = Query(None, description="Фильтр по статусу прочтения"),
        event_type: Optional[str] = Query(None, description="Фильтр по типу события"),
    ):
        return await self.notification_service.get_notifications(
            user_eid=current_user.eid,
            page=page,
            size=size,
            is_read=is_read,
            event_type=event_type,
        )

    @notification_router.get(
        "/stats",
        response_model=NotificationStatsSchema,
    )
    @exception_handler
    async def get_notification_stats(
        self,
        current_user: CurrentUser = Depends(CheckPermissionDep("notifications", "read")),
    ):
        return await self.notification_service.get_notification_stats(
            user_eid=current_user.eid
        )

    @notification_router.get(
        "/unread-count",
        response_model=int,
    )
    @exception_handler
    async def get_unread_count(
        self,
        current_user: CurrentUser = Depends(CheckPermissionDep("notifications", "read")),
    ):
        return await self.notification_service.get_unread_count(
            user_eid=current_user.eid
        )

    @notification_router.get(
        "/{notification_id}",
        response_model=NotificationSchema,
    )
    @exception_handler
    async def get_notification_by_id(
        self,
        notification_id: int,
        current_user: CurrentUser = Depends(CheckPermissionDep("notifications", "read")),
    ):
        return await self.notification_service.get_notification_by_id(
            notification_id=notification_id,
            user_eid=current_user.eid,
        )

    @notification_router.post(
        "/{notification_id}/read",
    )
    @exception_handler
    async def mark_as_read(
        self,
        notification_id: int,
        current_user: CurrentUser = Depends(CheckPermissionDep("notifications", "read")),
    ):

        return await self.notification_service.mark_as_read(
            notification_id=notification_id,
            user_eid=current_user.eid,
        )

    @notification_router.post(
        "/read-all",
    )
    @exception_handler
    async def mark_all_as_read(
        self,
        current_user: CurrentUser = Depends(CheckPermissionDep("notifications", "read")),
    ):
        return await self.notification_service.mark_all_as_read(
            user_eid=current_user.eid
        )

    @notification_router.delete(
        "/{notification_id}",
    )
    @exception_handler
    async def delete_notification(
        self,
        notification_id: int,
        current_user: CurrentUser = Depends(CheckPermissionDep("notifications", "manage")),
    ):
        return await self.notification_service.delete_notification(
            notification_id=notification_id,
            user_eid=current_user.eid,
        )

    @notification_router.get(
        "/preferences",
        response_model=NotificationPreferencesSchema,
    )
    @exception_handler
    async def get_preferences(
        self,
        current_user: CurrentUser = Depends(CheckPermissionDep("notifications", "read")),
    ):
        return await self.notification_service.get_preferences(
            user_eid=current_user.eid
        )

    @notification_router.patch(
        "/preferences",
        response_model=NotificationPreferencesSchema,
    )
    @exception_handler
    async def update_preferences(
        self,
        data: NotificationPreferencesUpdateSchema,
        current_user: CurrentUser = Depends(CheckPermissionDep("notifications", "manage")),
    ):
        return await self.notification_service.update_preferences(
            user_eid=current_user.eid,
            data=data,
        )

    @notification_router.post(
        "/",
        response_model=int,
    )
    @exception_handler
    async def create_notification(
        self,
        data: NotificationCreateSchema,
        current_user: CurrentUser = Depends(
            CheckPermissionDep("notifications", "manage", required_roles=["admin", "hr"])
        ),
    ):
        return await self.notification_service.create_notification(data=data)

    @notification_router.post(
        "/bulk",
        response_model=List[int],
    )
    @exception_handler
    async def create_notifications_bulk(
        self,
        data: NotificationBulkCreateSchema,
        current_user: CurrentUser = Depends(
            CheckPermissionDep("notifications", "manage", required_roles=["admin"])
        ),
    ):
        return await self.notification_service.create_notifications_bulk(
            notifications_data=data.notifications
        )

    @notification_router.delete(
        "/cleanup",
    )
    @exception_handler
    async def cleanup_old_notifications(
        self,
        days: int = Query(30, ge=1, description="Количество дней"),
        current_user: CurrentUser = Depends(
            CheckPermissionDep("notifications", "manage", required_roles=["admin"])
        ),
    ):
        return await self.notification_service.cleanup_old_notifications(
            days=days
        )

    @notification_router.post(
        "/bot/link",
        response_model=UserBotMappingSchema,
    )
    @exception_handler
    async def link_bot_account(
        self,
        data: UserBotMappingCreateSchema,
        current_user: CurrentUser = Depends(CheckPermissionDep("notifications", "manage")),
    ):

        return await self.notification_service.link_bot_account(
            user_eid=current_user.eid,
            band_chat_id=data.band_chat_id,
            band_user_id=data.band_user_id,
        )

    @notification_router.get(
        "/bot/mapping",
        response_model=UserBotMappingSchema,
    )
    @exception_handler
    async def get_bot_mapping(
        self,
        current_user: CurrentUser = Depends(CheckPermissionDep("notifications", "read")),
    ):
        return await self.notification_service.get_bot_mapping(
            user_eid=current_user.eid
        )

    @notification_router.delete(
        "/bot/unlink",
    )
    @exception_handler
    async def unlink_bot_account(
        self,
        current_user: CurrentUser = Depends(CheckPermissionDep("notifications", "manage")),
    ):
        return await self.notification_service.unlink_bot_account(
            user_eid=current_user.eid
        )

    @notification_router.post(
        "/bot/test",
    )
    @exception_handler
    async def send_test_notification(
        self,
        current_user: CurrentUser = Depends(CheckPermissionDep("notifications", "manage")),
    ):
        return await self.notification_service.send_test_notification(
            user_eid=current_user.eid
        )
