from jose import jwt, JWTError
from datetime import datetime
from typing import Dict, Any
from fastapi import HTTPException, status

from core.config.settings import get_settings


class TokenService:
    @staticmethod
    def validate_token(token: str) -> Dict[str, Any]:
        settings = get_settings()
        public_key = settings.KEYCLOAK_PUBLIC_KEY.replace("\\n", "\n")

        if not public_key.strip():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="KEYCLOAK_PUBLIC_KEY is not configured"
            )

        try:
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options={"verify_aud": False},
            )
            exp = payload.get("exp")
            if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )

    @staticmethod
    def get_user_info(token: str) -> Dict[str, Any]:
        payload = TokenService.validate_token(token)
        return {
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "username": payload.get("preferred_username"),
            "roles": payload.get("realm_access", {}).get("roles", []),
            "groups": payload.get("groups", []),
        }