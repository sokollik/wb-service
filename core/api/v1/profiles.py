from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.db import get_session
from core.api.deps import get_current_user_eid
from core.services.access_service import AccessService
from core.schemas.profile import ProfileOrm
from core.schemas.profile import ProfileRead
from core.models.employee import EmployeeOrm

router = APIRouter(prefix="/v1/profiles", tags=["Profiles"])


@router.get("/{employee_eid}", response_model=ProfileRead)
def read_profile(
    employee_eid: int,
    session: Session = Depends(get_session),
    current_user_eid: int = Depends(get_current_user_eid),
):
    target_employee = session.get(EmployeeOrm, employee_eid)
    if not target_employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    profile = session.query(ProfileOrm).filter(
        ProfileOrm.employee_id == employee_eid
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    access_service = AccessService(session, current_user_eid)
    can_view_phone = access_service.can_view_personal_phone(employee_eid)
    
    response_data = ProfileRead.model_validate(profile)
    if not can_view_phone:
        response_data.personal_phone = None

    return response_data