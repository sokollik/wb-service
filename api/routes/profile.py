# api/routes/profile.py
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import os
import asyncpg
from sqlalchemy.orm import selectinload
from datetime import date

from core.database import get_db
from core.models.emploee import EmployeeOrm, DepartmentOrm
from core.models.profile import ProfileOrm, ProfileProjectOrm, ProfileVacationOrm
from core.models.static import FileOrm

router = APIRouter(prefix="/api/profile", tags=["profile"])

# Pydantic модели для запросов и ответов
class ProfileResponse(BaseModel):
    # Основная информация
    eid: int
    full_name: str
    position: str
    work_email: str
    work_phone: Optional[str] = None
    work_band: Optional[str] = None
    
    # Отдел и структура
    department: Optional[str] = None
    department_hierarchy: Optional[List[str]] = None
    manager: Optional[Dict[str, Any]] = None
    hr_bp: Optional[Dict[str, Any]] = None
    
    # Редактируемые поля
    avatar_url: Optional[str] = None
    personal_phone: Optional[str] = None
    telegram: Optional[str] = None
    about_me: Optional[str] = None
    
    # Проекты
    projects: List[Dict[str, Any]] = []
    
    # Отпуск
    current_vacation: Optional[Dict[str, Any]] = None
    planned_vacations: List[Dict[str, Any]] = []
    
    class Config:
        from_attributes = True

class ProfileUpdate(BaseModel):
    personal_phone: Optional[str] = None
    telegram: Optional[str] = None
    about_me: Optional[str] = None

class ProjectCreate(BaseModel):
    name: str
    position: str
    start_d: Optional[date] = None
    end_d: Optional[date] = None
    link: Optional[str] = None

class VacationCreate(BaseModel):
    start_date: date
    end_date: date
    comment: Optional[str] = None
    substitute_eid: Optional[int] = None


@router.get("/diagnostics")
async def diagnostics():
    """Полная диагностика"""
    import socket
    from core.config.settings import get_database_settings
    
    settings = get_database_settings()
    
    results = {
        "settings": {
            "host": settings.host,
            "port": settings.port,
            "user": settings.user,
            "database": settings.name,
            "password_length": len(settings.password) if settings.password else 0
        },
        "network": {},
        "docker": {}
    }
    
    # Проверка сети
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((settings.host, int(settings.port)))
        sock.close()
        results["network"]["port_accessible"] = result == 0
    except Exception as e:
        results["network"]["port_accessible"] = f"Error: {e}"
    
    # Проверка через asyncpg
    try:
        import asyncpg
        conn = await asyncpg.connect(
            host=settings.host,
            port=int(settings.port),
            user=settings.user,
            password=settings.password,
            database=settings.name,
            timeout=5
        )
        db_version = await conn.fetchval('SELECT version()')
        await conn.close()
        results["database"]["connection"] = "✅ SUCCESS"
        results["database"]["version"] = db_version.split()[0]
    except Exception as e:
        results["database"]["connection"] = f"❌ FAILED: {e}"
    
    return results
    
@router.get("/check-data")
async def check_data():
    """Проверим есть ли данные в employee таблице"""
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432, 
            user='postgres',
            password='postgres',
            database='postgres'
        )
        
        # Проверим таблицы
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        # Проверим есть ли сотрудники
        employees_count = await conn.fetchval("SELECT COUNT(*) FROM employee")
        
        await conn.close()
        
        return {
            "tables": [t['table_name'] for t in tables],
            "employees_count": employees_count
        }
    except Exception as e:
        return {"error": str(e)}

# 1. Показать свой профиль
@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(db: AsyncSession = Depends(get_db)):
    """Получить полные данные текущего пользователя"""
    current_employee_eid = 1001  #  Заменить на данные из Keycloak
    
    try:
        # Получаем сотрудника со всеми связями
        stmt = (
            select(EmployeeOrm)
            .options(
                selectinload(EmployeeOrm.department),
                selectinload(EmployeeOrm.manager),
                selectinload(EmployeeOrm.hrbp),
                selectinload(EmployeeOrm.profile).selectinload(ProfileOrm.avatar),
                selectinload(EmployeeOrm.profile).selectinload(ProfileOrm.projects),
                selectinload(EmployeeOrm.profile).selectinload(ProfileOrm.vacations)
            )
            .where(EmployeeOrm.eid == current_employee_eid)
        )
        
        result = await db.execute(stmt)
        employee = result.scalar_one_or_none()
        
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        return await _format_profile_response(employee, full_access=True)
    
    except Exception as e:
        # Логируем ошибку для диагностики
        print(f"Error in /me endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# 2. Показать чужой профиль
@router.get("/{employee_eid}", response_model=ProfileResponse)
async def get_employee_profile(employee_eid: int, db: AsyncSession = Depends(get_db)):
    """Получить данные другого сотрудника (ограниченный доступ)"""
    current_employee_eid = 1001  # TODO: Заменить на данные из Keycloak
    
    # Проверяем права доступа (упрощенно)
    has_full_access = await _check_profile_access(current_employee_eid, employee_eid, db)
    
    stmt = (
        select(EmployeeOrm)
        .options(
            selectinload(EmployeeOrm.department),
            selectinload(EmployeeOrm.manager),
            selectinload(EmployeeOrm.hrbp),
            selectinload(EmployeeOrm.profile).selectinload(ProfileOrm.avatar),
            selectinload(EmployeeOrm.profile).selectinload(ProfileOrm.projects),
        )
        .where(EmployeeOrm.eid == employee_eid)
    )
    
    result = await db.execute(stmt)
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return await _format_profile_response(employee, full_access=has_full_access)

# 3. Редактировать профиль
@router.put("/me")
async def update_my_profile(
    update_data: ProfileUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновить редактируемые поля профиля"""
    current_employee_eid = 1001  # TODO: Заменить на данные из Keycloak
    
    # Находим профиль сотрудника
    stmt = select(ProfileOrm).where(ProfileOrm.employee_id == current_employee_eid)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    
    # Если профиля нет - создаем
    if not profile:
        profile = ProfileOrm(employee_id=current_employee_eid)
        db.add(profile)
    
    # Обновляем разрешенные поля
    if update_data.personal_phone is not None:
        profile.personal_phone = update_data.personal_phone
    if update_data.telegram is not None:
        profile.telegram = update_data.telegram
    if update_data.about_me is not None:
        profile.about_me = update_data.about_me
    
    await db.commit()
    await db.refresh(profile)
    
    return {"message": "Profile updated successfully", "updated_fields": update_data.dict(exclude_unset=True)}

# 5. Ссылка на профиль
@router.get("/share/{employee_eid}")
async def get_profile_share_link(employee_eid: int, db: AsyncSession = Depends(get_db)):
    """Получить share-ссылку на профиль сотрудника"""
    
    # Проверяем что сотрудник существует
    stmt = select(EmployeeOrm).where(EmployeeOrm.eid == employee_eid)
    result = await db.execute(stmt)
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Генерируем deeplink (в реальности это может быть короткая ссылка)
    share_link = f"https://portal.wbbank.ru/profile/{employee_eid}"
    
    return {
        "employee_eid": employee_eid,
        "full_name": employee.full_name,
        "share_link": share_link,
        "qr_code_url": f"/api/qr/{employee_eid}"  # Для генерации QR кода
    }

# Вспомогательные функции
async def _format_profile_response(employee: EmployeeOrm, full_access: bool = True) -> Dict[str, Any]:
    """Форматирует ответ профиля в зависимости от прав доступа"""
    
    # Базовая информация (доступна всем)
    response = {
        "eid": employee.eid,
        "full_name": employee.full_name,
        "position": employee.position,
        "work_email": employee.work_email,
        "work_phone": employee.work_phone,
        "work_band": employee.work_band,
        "department": employee.department.name if employee.department else None,
        "manager": {
            "eid": employee.manager.eid,
            "full_name": employee.manager.full_name,
            "position": employee.manager.position
        } if employee.manager else None,
        "hr_bp": {
            "eid": employee.hrbp.eid,
            "full_name": employee.hrbp.full_name,
            "position": employee.hrbp.position
        } if employee.hrbp else None,
    }
    
    # Редактируемые поля (только при full_access или самому себе)
    if full_access and employee.profile:
        response.update({
            "avatar_url": f"/api/files/{employee.profile.avatar_id}" if employee.profile.avatar_id else None,
            "personal_phone": employee.profile.personal_phone,
            "telegram": employee.profile.telegram,
            "about_me": employee.profile.about_me,
            "projects": [
                {
                    "id": project.id,
                    "name": project.name,
                    "position": project.position,
                    "start_d": project.start_d,
                    "end_d": project.end_d,
                    "link": project.link
                } for project in employee.profile.projects
            ] if employee.profile.projects else [],
        })
        
        # Отпуска (только текущие и планируемые)
        if hasattr(employee.profile, 'vacations'):
            current_vacations = [v for v in employee.profile.vacations if not v.is_planned and v.is_official]
            planned_vacations = [v for v in employee.profile.vacations if v.is_planned]
            
            response["current_vacation"] = {
                "start_date": current_vacations[0].start_date,
                "end_date": current_vacations[0].end_date,
                "comment": current_vacations[0].comment
            } if current_vacations else None
            
            response["planned_vacations"] = [
                {
                    "start_date": vac.start_date,
                    "end_date": vac.end_date,
                    "comment": vac.comment
                } for vac in planned_vacations
            ]
    
    return response

async def _check_profile_access(current_eid: int, target_eid: int, db: AsyncSession) -> bool:
    """Проверяет права доступа к профилю"""
    # TODO: Реализовать реальную проверку прав
    # Сейчас упрощенно - полный доступ только к своему профилю
    return current_eid == target_eid