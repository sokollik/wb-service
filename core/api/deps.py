from typing import List

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel

from core.common.token_service import TokenService
from core.middleware import JWTBearer

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
