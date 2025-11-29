from datetime import date
from typing import Optional, List
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
