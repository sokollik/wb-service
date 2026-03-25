from fastapi import HTTPException, status
from jose import JWTError, jwt

from core.config.settings import get_settings


class TokenService:
    @staticmethod
    def validate_token(token: str) -> dict[str, any]:
        settings = get_settings()
        raw_key = settings.KEYCLOAK_PUBLIC_KEY.replace("\\n", "\n").strip()

        if not raw_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="KEYCLOAK_PUBLIC_KEY is not configured",
            )

        if not raw_key.startswith("-----BEGIN"):
            public_key = (
                "-----BEGIN PUBLIC KEY-----\n"
                + raw_key
                + "\n-----END PUBLIC KEY-----"
            )
        else:
            public_key = raw_key

        try:
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options={"verify_aud": False},
            )
            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
            )

    @staticmethod
    def get_user_info(token: str) -> dict[str, any]:
        print(23242424242432)
        payload = TokenService.validate_token(token)
        return {
            "eid": payload.get("sub"),
            "email": payload.get("email"),
            "username": payload.get("preferred_username"),
            "roles": payload.get("realm_access", {}).get("roles", []),
        }
