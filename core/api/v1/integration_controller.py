from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request, HTTPException
from fastapi_restful.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession

from core.api.deps import CurrentUser, require_roles, CheckPermissionDep
from core.services.integrations import KeycloakSSOService, ThesisIntegrationService
from core.utils.common_util import exception_handler
from core.utils.db_util import get_session_obj

integration_router = APIRouter(prefix="/integrations", tags=["Integrations"])


@cbv(integration_router)
class IntegrationController:
    def __init__(self, session: AsyncSession = Depends(get_session_obj)):
        self.session = session
        self.keycloak_service = KeycloakSSOService(session)
        self.thesis_service = ThesisIntegrationService(session)

    @integration_router.post(
        "/keycloak/webhook",
        summary="Webhook от Keycloak для синхронизации пользователей",
        description="Получение событий от Keycloak о создании/обновлении/удалении пользователей",
    )
    @exception_handler
    async def handle_keycloak_webhook(
        self,
        request: Request,
        x_keycloak_event: Optional[str] = Query(None, alias="X-Keycloak-Event"),
    ):

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Authorization header required",
            )
        
        event_type = x_keycloak_event or request.headers.get("X-Keycloak-Event")
        
        if not event_type:
            raise HTTPException(
                status_code=400,
                detail="X-Keycloak-Event header is required",
            )
        
        try:
            payload = await request.json()
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON payload",
            )
        
        result = await self.keycloak_service.handle_keycloak_webhook(
            event_type=event_type,
            payload=payload,
        )
        
        return result

    @integration_router.post(
        "/keycloak/sync",
        summary="Запустить периодическую синхронизацию с Keycloak",
        description="Синхронизация пользователей с Keycloak API (только admin)",
    )
    @exception_handler
    async def trigger_keycloak_sync(
        self,
        limit: int = Query(100, ge=1, le=1000),
        current_user: CurrentUser = Depends(require_roles(["admin"])),
    ):

        synced_count = await self.keycloak_service.periodic_sync(limit=limit)
        return {
            "success": True,
            "synced_count": synced_count,
        }

    @integration_router.get(
        "/thesis/document/{thesis_doc_id}/link",
        summary="Получить ссылку для перехода к документу в Тезис",
        description="Генерация временной ссылки с OAuth2 token для доступа к документу в Тезис",
    )
    @exception_handler
    async def get_thesis_document_link(
        self,
        thesis_doc_id: str,
        local_document_id: Optional[int] = Query(None),
        current_user: CurrentUser = Depends(CheckPermissionDep("documents", "read")),
        request: Request = None,
    ):
        user_agent = request.headers.get("User-Agent", "") if request else None
        ip_address = request.client.host if request else None
        
        result = await self.thesis_service.generate_document_link(
            user_eid=current_user.eid,
            thesis_document_id=thesis_doc_id,
            local_document_id=local_document_id,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        
        return {
            "redirect_url": result["redirect_url"],
            "thesis_document_id": result["thesis_document_id"],
            "log_id": result["log_id"],
            "expires_in": 300,  # 5 минут
        }

    @integration_router.get(
        "/thesis/logs",
        summary="Получить логи переходов в Тезис",
        description="Просмотр истории переходов пользователей в систему Тезис (только admin)",
    )
    @exception_handler
    async def get_thesis_logs(
        self,
        user_eid: Optional[str] = Query(None),
        document_id: Optional[int] = Query(None),
        status: Optional[str] = Query(None),
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        current_user: CurrentUser = Depends(
            CheckPermissionDep("documents", "manage", required_roles=["admin"])
        ),
    ):
        logs, total = await self.thesis_service.get_transition_logs(
            user_eid=user_eid,
            document_id=document_id,
            status=status,
            limit=limit,
            offset=offset,
        )
        
        return {
            "total": total,
            "logs": [
                {
                    "id": log.id,
                    "user_eid": log.user_eid,
                    "thesis_document_id": log.thesis_document_id,
                    "local_document_id": log.local_document_id,
                    "status": log.status,
                    "error_message": log.error_message,
                    "created_at": log.created_at.isoformat(),
                    "completed_at": log.completed_at.isoformat() if log.completed_at else None,
                }
                for log in logs
            ],
            "limit": limit,
            "offset": offset,
        }

    @integration_router.get(
        "/thesis/stats",
        summary="Статистика переходов в Тезис",
        description="Получение статистики по переходам в систему Тезис (только admin)",
    )
    @exception_handler
    async def get_thesis_stats(
        self,
        current_user: CurrentUser = Depends(
            CheckPermissionDep("documents", "manage", required_roles=["admin"])
        ),
    ):
        """Получить статистику переходов в Тезис"""
        from sqlalchemy import select, func
        from core.models.integrations import ThesisIntegrationLogOrm

        total_result = await self.session.execute(
            select(func.count(ThesisIntegrationLogOrm.id))
        )
        total = total_result.scalar() or 0
        
        success_result = await self.session.execute(
            select(func.count(ThesisIntegrationLogOrm.id)).where(
                ThesisIntegrationLogOrm.status == "success"
            )
        )
        success = success_result.scalar() or 0
        
        failed_result = await self.session.execute(
            select(func.count(ThesisIntegrationLogOrm.id)).where(
                ThesisIntegrationLogOrm.status == "failed"
            )
        )
        failed = failed_result.scalar() or 0
        
        from datetime import datetime, timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_result = await self.session.execute(
            select(func.count(ThesisIntegrationLogOrm.id)).where(
                ThesisIntegrationLogOrm.created_at >= yesterday
            )
        )
        recent = recent_result.scalar() or 0
        
        return {
            "total_transitions": total,
            "successful": success,
            "failed": failed,
            "success_rate": round(success / total * 100, 2) if total > 0 else 0,
            "last_24_hours": recent,
        }
