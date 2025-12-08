from datetime import date, datetime
from typing import Any, Dict, List, Union

from pydantic import BaseModel, Field


class ProjectSchema(BaseModel):
    id: int = Field(...)
    name: str | None = Field(None)
    start_d: date | None = Field(None)
    end_d: date | None = Field(None)
    position: str | None = Field(None)
    link: str | None = Field(None)


class VacationSchema(BaseModel):
    id: int = Field(...)
    is_planned: bool = Field(...)
    start_date: date = Field(...)
    end_date: date = Field(...)
    substitute: str | None = Field(None)
    comment: str | None = Field(None)
    is_official: bool = Field(...)


class ProfileSchema(BaseModel):
    eid: int = Field(..., description="ID работника")
    full_name: str = Field(...)
    avatar_id: int | None = Field(None)
    position: str = Field(...)
    department: str = Field(...)
    birth_date: date = Field(...)
    hire_date: date = Field(...)
    personal_phone: str = Field(...)
    work_phone: str = Field(...)
    work_email: str = Field(...)
    work_band: str = Field(...)
    telegram: str = Field(...)
    manager_name: str | None = Field(None)
    hr_name: str | None = Field(None)
    about_me: str | None = Field(None)
    projects: list[ProjectSchema] | None = Field(None)
    vacations: list[VacationSchema] | None = Field(None)


class ProjectUpdateSchema(BaseModel):
    name: str | None = Field(None)
    start_d: date | None = Field(None)
    end_d: date | None = Field(None)
    position: str | None = Field(None)
    link: str | None = Field(None)


class ProfileUpdateSchema(BaseModel):
    avatar_id: int | None = Field(None)
    personal_phone: str | None = Field(None)
    telegram: str | None = Field(None)
    about_me: str | None = Field(None)
    projects: list[ProjectUpdateSchema] | None = Field(None)


class ProfileChangeLogSchema(BaseModel):
    id: int = Field(...)
    profile_id: int = Field(...)
    changed_by_eid: int = Field(...)
    changed_at: datetime = Field(...)
    table_name: str = Field(...)
    record_id: int | None = Field(None)
    field_name: str = Field(...)

    old_value: Union[str, Dict[str, Any], List[Any], bool, int] | None = Field(None)
    new_value: Union[str, Dict[str, Any], List[Any], bool, int] | None = Field(None)

    operation: Any = Field(...)

    class Config:
        from_attributes = True
