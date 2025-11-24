from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from core.db import get_session
from core.models.auth import AuthTokenOrm

security = HTTPBearer()

def get_current_user_eid(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
) -> int:
    token = credentials.credentials
    
    auth_token = session.query(AuthTokenOrm).filter(
        AuthTokenOrm.token == token
    ).first()
    
    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return auth_token.employee_eid