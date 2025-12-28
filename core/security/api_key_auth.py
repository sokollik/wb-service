from fastapi import HTTPException, status, Header, Depends
from core.config.settings import get_settings

def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    settings = get_settings()
    if not settings.API_KEY_1C:
        raise HTTPException(status_code=500, detail="API key not configured")
    if x_api_key != settings.API_KEY_1C:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key"
        )
    return True