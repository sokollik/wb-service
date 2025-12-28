from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class ProjectSchema(BaseModel):
    id: int
    name: str | None = None
    start_d: date | None = None
    end_d: date | None = None
    position: str | None = None
    link: str | None = None

    class Config:
        from_attributes = True


class VacationSchema(BaseModel):
    id: int
    is_planned: bool
    start_date: date
    end_date: date
    substitute: str | None = None
    comment: str | None = None
    is_official: bool

    class Config:
        from_attributes = True


class ProfileSchema(BaseModel):
    eid: int
    full_name: str
    avatar_id: int | None = None
    position: str
    org_unit: str
    birth_date: date
    hire_date: date
    personal_phone: str | None = None
    work_phone: str | None = None
    work_email: str
    work_band: str | None = None
    telegram: str | None = None
    manager_name: str | None = None
    hr_name: str | None = None
    about_me: str | None = None
    projects: list[ProjectSchema] | None = None
    vacations: list[VacationSchema] | None = None

    class Config:
        from_attributes = True


class ProjectUpdateSchema(BaseModel):
    name: str | None = None
    start_d: date | None = None
    end_d: date | None = None
    position: str | None = None
    link: str | None = None


class ProfileUpdateSchema(BaseModel):
    avatar_id: int | None = None
    personal_phone: str | None = None
    telegram: str | None = None
    about_me: str | None = None
    projects: list[ProjectUpdateSchema] | None = None


class ProfileChangeLogSchema(BaseModel):
    id: int
    profile_id: int
    changed_by_eid: int
    changed_at: datetime
    table_name: str
    record_id: int | None = None
    field_name: str
    old_value: Union[str, Dict[str, Any], List[Any], bool, int] | None = None
    new_value: Union[str, Dict[str, Any], List[Any], bool, int] | None = None
    operation: Any

    class Config:
        from_attributes = True


class ProfileExportFilter(BaseModel):
    fields: str | None = None

    @field_validator("fields")
    @classmethod
    def split_comma_string(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v


class EmployeeSuggestion(BaseModel):
    """Предложение для автодополнения"""
    eid: int
    full_name: str
    position: str
    department: str


class EmployeeSearchResult(BaseModel):
    """Результат поиска сотрудника"""
    eid: int
    full_name: str
    position: str
    work_email: str | None = None
    work_phone: str | None = None
    organization_unit_id: str | None = None
    organization_unit_name: str | None = None
    work_band: str | None = None
    score: float


class SearchResponse(BaseModel):
    """Ответ от поиска"""
    total: int
    results: List[EmployeeSearchResult]
    error: str | None = None


class SuggestResponse(BaseModel):
    """Ответ от автодополнения"""
    suggestions: List[EmployeeSuggestion]