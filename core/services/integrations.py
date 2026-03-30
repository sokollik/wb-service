import base64
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlencode, urljoin

import httpx
from jose import jwt, JWTError
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.settings import get_settings
from core.models.integrations import (
    KeycloakUserSyncOrm,
    ThesisCredentialsOrm,
    ThesisIntegrationLogOrm,
)
from core.models.emploee import EmployeeOrm


class KeycloakSSOService:
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()
        self._public_key = None
        self._public_key_expires_at = None
    
    def _get_public_key(self) -> str:
        if (
            self._public_key and 
            self._public_key_expires_at and 
            datetime.utcnow() < self._public_key_expires_at
        ):
            return self._public_key
        
        raw_key = self.settings.KEYCLOAK_PUBLIC_KEY.replace("\\n", "\n").strip()
        
        if not raw_key:
            raise ValueError("KEYCLOAK_PUBLIC_KEY is not configured")
        
        if not raw_key.startswith("-----BEGIN"):
            self._public_key = (
                "-----BEGIN PUBLIC KEY-----\n"
                + raw_key
                + "\n-----END PUBLIC KEY-----"
            )
        else:
            self._public_key = raw_key
        
        self._public_key_expires_at = datetime.utcnow() + timedelta(hours=1)
        return self._public_key
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        public_key = self._get_public_key()
        
        try:
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options={"verify_aud": False},
            )
            return payload
        except JWTError as e:
            raise JWTError(f"Invalid token: {str(e)}")
    
    def extract_user_info(self, token_payload: Dict[str, Any]) -> Dict[str, Any]:

        return {
            "eid": token_payload.get("sub"),
            "email": token_payload.get("email"),
            "username": token_payload.get("preferred_username"),
            "full_name": token_payload.get("name"),
            "given_name": token_payload.get("given_name"),
            "family_name": token_payload.get("family_name"),
            "roles": token_payload.get("realm_access", {}).get("roles", []),
            "email_verified": token_payload.get("email_verified", False),
        }
    
    async def check_user_active(self, user_eid: str) -> bool:

        result = await self.session.execute(
            select(KeycloakUserSyncOrm).where(
                KeycloakUserSyncOrm.user_eid == user_eid
            )
        )
        sync_record = result.scalar_one_or_none()
        
        if sync_record:
            return not sync_record.is_fired
        
        employee = await self.session.get(EmployeeOrm, user_eid)
        if employee:
            return not employee.is_fired
        
        return False
    
    async def sync_user_from_keycloak(
        self,
        user_eid: str,
        keycloak_data: Dict[str, Any],
    ) -> KeycloakUserSyncOrm:

        result = await self.session.execute(
            select(KeycloakUserSyncOrm).where(
                KeycloakUserSyncOrm.user_eid == user_eid
            )
        )
        sync_record = result.scalar_one_or_none()
        
        if sync_record:
            sync_record.email = keycloak_data.get("email", sync_record.email)
            sync_record.username = keycloak_data.get("username", sync_record.username)
            sync_record.full_name = keycloak_data.get("full_name", sync_record.full_name)
            sync_record.is_fired = keycloak_data.get("is_fired", sync_record.is_fired)
            sync_record.is_active = not sync_record.is_fired
            sync_record.last_sync_at = datetime.utcnow()
            
            if sync_record.is_fired:
                sync_record.fired_at = datetime.utcnow()
        else:
            sync_record = KeycloakUserSyncOrm(
                user_eid=user_eid,
                email=keycloak_data.get("email"),
                username=keycloak_data.get("username"),
                full_name=keycloak_data.get("full_name"),
                is_fired=keycloak_data.get("is_fired", False),
                is_active=not keycloak_data.get("is_fired", False),
                last_sync_at=datetime.utcnow(),
            )
            self.session.add(sync_record)
        
        await self.session.flush()
        return sync_record
    
    async def handle_keycloak_webhook(
        self,
        event_type: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:

        user_eid = payload.get("userId") or payload.get("sub")
        
        if not user_eid:
            return {"success": False, "error": "user_eid not found"}
        
        if event_type in ["USER_DISABLED", "USER_DELETED"]:

            sync_data = {
                "is_fired": True,
                "fired_at": datetime.utcnow(),
            }
            await self.sync_user_from_keycloak(user_eid, sync_data)
            return {"success": True, "action": "user_fired"}
        
        elif event_type in ["USER_ENABLED", "USER_CREATED", "USER_UPDATED"]:
            sync_data = {
                "email": payload.get("email"),
                "username": payload.get("username"),
                "full_name": payload.get("full_name"),
                "is_fired": False,
            }
            await self.sync_user_from_keycloak(user_eid, sync_data)
            return {"success": True, "action": "user_synced"}
        
        return {"success": False, "error": f"Unknown event type: {event_type}"}
    
    async def periodic_sync(self, limit: int = 100) -> int:
        result = await self.session.execute(
            select(KeycloakUserSyncOrm).where(
                KeycloakUserSyncOrm.last_sync_at < datetime.utcnow() - timedelta(hours=1)
            ).limit(limit)
        )
        users_to_sync = result.scalars().all()
        
        synced_count = 0
        for user in users_to_sync:
            user.last_sync_at = datetime.utcnow()
            synced_count += 1
        
        await self.session.commit()
        return synced_count


class ThesisIntegrationService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()
        self._token_cache: Optional[Dict[str, Any]] = None
    
    async def _get_credentials(self) -> Optional[ThesisCredentialsOrm]:
        result = await self.session.execute(
            select(ThesisCredentialsOrm).where(
                ThesisCredentialsOrm.is_active == True
            ).order_by(ThesisCredentialsOrm.updated_at.desc())
        )
        return result.scalar_one_or_none()
    
    async def _get_or_refresh_token(self) -> str:

        credentials = await self._get_credentials()
        
        if not credentials:
            raise ValueError("Thesis credentials not configured")
        
        if (
            credentials.access_token and
            credentials.token_expires_at and
            datetime.utcnow() < credentials.token_expires_at - timedelta(minutes=5)
        ):
            return credentials.access_token
        
        token_url = urljoin(
            self.settings.THESIS_BASE_URL or "https://thesis.corporate.ru",
            "/oauth2/token"
        )
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": credentials.client_id,
                    "client_secret": credentials.client_secret,
                    "scope": "api:read api:write",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            
            token_data = response.json()
            
            credentials.access_token = token_data.get("access_token")
            credentials.refresh_token = token_data.get("refresh_token")
            credentials.token_expires_at = datetime.utcnow() + timedelta(
                seconds=token_data.get("expires_in", 3600)
            )
            credentials.last_used_at = datetime.utcnow()
            
            await self.session.flush()
            
            return credentials.access_token
    
    def _generate_temp_token(
        self,
        user_eid: str,
        thesis_document_id: str,
        expires_in: int = 300,
    ) -> str:

        settings = get_settings()
        
        payload = {
            "sub": user_eid,
            "thesis_doc_id": thesis_document_id,
            "exp": datetime.utcnow() + timedelta(seconds=expires_in),
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(16),
        }
        
        token = jwt.encode(
            payload,
            settings.THESIS_JWT_SECRET or settings.KEYCLOAK_CLIENT_SECRET,
            algorithm="HS256",
        )
        
        return token
    
    async def generate_document_link(
        self,
        user_eid: str,
        thesis_document_id: str,
        local_document_id: Optional[int] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Dict[str, str]:

        log_entry = ThesisIntegrationLogOrm(
            user_eid=user_eid,
            thesis_document_id=thesis_document_id,
            local_document_id=local_document_id,
            user_agent=user_agent,
            ip_address=ip_address,
            status="pending",
        )
        self.session.add(log_entry)
        await self.session.flush()
        
        try:
            sso_service = KeycloakSSOService(self.session)
            is_active = await sso_service.check_user_active(user_eid)
            
            if not is_active:
                raise ValueError("Пользователь не активен (возможно уволен)")
            
            access_token = await self._get_or_refresh_token()
            
            temp_token = self._generate_temp_token(
                user_eid=user_eid,
                thesis_document_id=thesis_document_id,
            )
            
            base_url = self.settings.THESIS_BASE_URL or "https://thesis.corporate.ru"
            redirect_url = urljoin(
                base_url,
                f"/documents/{thesis_document_id}",
            )
            redirect_url += f"?token={temp_token}&oauth_token={access_token}"
            
            log_entry.access_token = temp_token
            log_entry.token_expires_at = datetime.utcnow() + timedelta(minutes=5)
            log_entry.redirect_url = redirect_url
            log_entry.status = "success"
            log_entry.completed_at = datetime.utcnow()
            
            await self.session.flush()
            
            return {
                "redirect_url": redirect_url,
                "log_id": str(log_entry.id),
                "thesis_document_id": thesis_document_id,
            }
            
        except Exception as e:
            log_entry.status = "failed"
            log_entry.error_message = str(e)
            log_entry.completed_at = datetime.utcnow()
            await self.session.flush()
            
            raise
    
    async def get_transition_logs(
        self,
        user_eid: Optional[str] = None,
        document_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ThesisIntegrationLogOrm], int]:

        query = select(ThesisIntegrationLogOrm)
        
        if user_eid:
            query = query.where(ThesisIntegrationLogOrm.user_eid == user_eid)
        if document_id:
            query = query.where(
                ThesisIntegrationLogOrm.local_document_id == document_id
            )
        if status:
            query = query.where(ThesisIntegrationLogOrm.status == status)
        
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0
        
        query = query.order_by(
            ThesisIntegrationLogOrm.created_at.desc()
        ).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        logs = result.scalars().all()
        
        return list(logs), total
