from functools import wraps
from typing import List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.common.token_service import TokenService
from core.services.rbac_service import RBACService
from core.utils.db_util import get_session_obj


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearer, self
        ).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme.",
                )
            token = credentials.credentials
            try:
                TokenService.validate_token(token)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
                )
            return token
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing",
            )


def CheckPermission(
    resource: str,
    action: str,
    required_roles: Optional[List[str]] = None,
):

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: Request, **kwargs):
            from core.api.deps import get_current_user, CurrentUser
            
            current_user: Optional[CurrentUser] = kwargs.get("current_user")
            
            if not current_user:
                current_user = getattr(request.state, "current_user", None)
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Требуется аутентификация",
                )
            
            session = kwargs.get("session")
            if not session:
                session = await get_session_obj().__anext__()
            
            try:
                rbac_service = RBACService(session)

                await rbac_service.enforce_permission(
                    user_eid=current_user.eid,
                    resource=resource,
                    action=action,
                    required_roles=required_roles,
                )
            finally:
                if not kwargs.get("session"):
                    await session.close()
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def RequireScope(
    org_unit_field: str = "org_unit_id",
    owner_field: Optional[str] = None,
    required_roles: Optional[List[str]] = None,
):

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: Request, **kwargs):
            from core.api.deps import get_current_user, CurrentUser
            
            current_user: Optional[CurrentUser] = kwargs.get("current_user")
            
            if not current_user:
                current_user = getattr(request.state, "current_user", None)
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Требуется аутентификация",
                )
            
            org_unit_id = kwargs.get(org_unit_field)
            if org_unit_id is None:
                org_unit_id = request.query_params.get(org_unit_field) or \
                              request.path_params.get(org_unit_field)
            
            if org_unit_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Параметр '{org_unit_field}' не найден",
                )
            
            owner_eid = kwargs.get(owner_field) if owner_field else None
            
            session = kwargs.get("session")
            if not session:
                session = await get_session_obj().__anext__()
            
            try:
                rbac_service = RBACService(session)
                
                await rbac_service.enforce_scope(
                    curator_eid=current_user.eid,
                    org_unit_id=int(org_unit_id),
                    owner_eid=owner_eid,
                )
            finally:
                if not kwargs.get("session"):
                    await session.close()
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def CheckRole(required_roles: List[str]):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: Request, **kwargs):
            from core.api.deps import get_current_user, CurrentUser
            
            current_user: Optional[CurrentUser] = kwargs.get("current_user")
            
            if not current_user:
                current_user = getattr(request.state, "current_user", None)
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Требуется аутентификация",
                )
            
            if not any(role in current_user.roles for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Требуется одна из ролей: {required_roles}",
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
