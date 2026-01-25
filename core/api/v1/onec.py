from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from core.security.api_key_auth import verify_api_key

router = APIRouter(prefix="/api/v1/1c", tags=["1C Integration"])

class OneCEmployee(BaseModel):
    id_1c: str
    full_name: str
    email: str
    department: str
    position: str
    is_active: bool

@router.post("/employees")
async def receive_employees(
    employees: List[OneCEmployee],
    _: bool = Depends(verify_api_key)
):
    return {
        "status": "success",
        "received": len(employees),
        "message": "Данные от 1С успешно получены"
    }