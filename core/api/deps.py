from typing import List, Optional
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from core.common.token_service import TokenService
from core.middleware import JWTBearer
from core.services.rbac_service import RBACService
from core.utils.db_util import get_session_obj

jwt_bearer = JWTBearer()


class CurrentUser(BaseModel):
    eid: str
    email: str | None = None
    username: str | None = None
    roles: List[str] = []


def get_current_user(token: str = Depends(jwt_bearer)) -> CurrentUser:
    user_info = TokenService.get_user_info(token)
    print(user_info)
    if not user_info.get("eid"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token does not contain user ID",
        )
    return CurrentUser(**user_info)


def require_roles(required_roles: List[str]):
    def role_checker(
        user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if not any(role in user.roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Требуется одна из ролей: {required_roles}",
            )
        return user

    return role_checker


def get_rbac_service(session=Depends(get_session_obj)) -> RBACService:
    return RBACService(session=session)


def CheckPermissionDep(
    resource: str,
    action: str,
    required_roles: Optional[List[str]] = None,
):
    async def permission_checker(
        current_user: CurrentUser = Depends(get_current_user),
        session=Depends(get_session_obj),
    ):
        rbac_service = RBACService(session)
        
        await rbac_service.enforce_permission(
            user_eid=current_user.eid,
            resource=resource,
            action=action,
            required_roles=required_roles,
        )
        
        return current_user
    
    return permission_checker


def RequireScopeDep(
    org_unit_field: str = "org_unit_id",
    owner_field: Optional[str] = None,
):
    async def scope_checker(
        current_user: CurrentUser = Depends(get_current_user),
        session=Depends(get_session_obj),
        org_unit_id: Optional[int] = None,
    ):
        if org_unit_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Параметр '{org_unit_field}' не найден",
            )
        
        rbac_service = RBACService(session)
        
        await rbac_service.enforce_scope(
            curator_eid=current_user.eid,
            org_unit_id=org_unit_id,
        )
        
        return current_user
    
    return scope_checker
