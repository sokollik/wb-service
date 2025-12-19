from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field

from core.models.enums import OrgUnitType


class OrgUnitManagerSchema(BaseModel):
    eid: int = Field(..., description="EID руководителя")
    full_name: str = Field(..., description="ФИО руководителя")
    position: str = Field(..., description="Должность руководителя")
    manager_avatar_id: Optional[int] = Field(None)

class OrgUnitBaseSchema(BaseModel):
    """Базовая схема для подразделения."""
    id: int = Field(..., description="ID подразделения")
    name: str = Field(..., description="Название подразделения")
    unit_type: OrgUnitType = Field(..., description="Тип структурной единицы")
    parent_id: Optional[int] = Field(None, description="ID родительского подразделения")
    
    is_temporary: bool = Field(False, description="Флаг временного подразделения")
    start_date: Optional[date] = Field(None, description="Дата начала (для временных)")
    end_date: Optional[date] = Field(None, description="Дата окончания (для временных)")
    
    manager: Optional[OrgUnitManagerSchema] = Field(None, description="Руководитель подразделения")


class OrgUnitHierarchySchema(BaseModel):
    id: int = Field(..., description="ID подразделения")
    name: str = Field(..., description="Название подразделения")
    unit_type: OrgUnitType = Field(..., description="Тип структурной единицы")
    parent_id: Optional[int] = Field(None, description="ID родительского подразделения")
    
    is_temporary: bool = Field(False, description="Флаг временного подразделения")
    start_date: Optional[date] = Field(None, description="Дата начала (для временных)")
    end_date: Optional[date] = Field(None, description="Дата окончания (для временных)")
    
    manager: Optional[OrgUnitManagerSchema] = Field(None, description="Руководитель подразделения")
    children: List["OrgUnitHierarchySchema"] = Field([], description="Список дочерних подразделений")

OrgUnitHierarchySchema.model_rebuild()
