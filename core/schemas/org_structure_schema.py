from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, ConfigDict

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

    manager: Optional[OrgUnitManagerSchema] = Field(
        None, description="Руководитель подразделения"
    )

    model_config = ConfigDict(from_attributes=True)


class OrgUnitHierarchySchema(BaseModel):
    id: int = Field(..., description="ID подразделения")
    name: str = Field(..., description="Название подразделения")
    unit_type: OrgUnitType = Field(..., description="Тип структурной единицы")
    parent_id: Optional[int] = Field(None, description="ID родительского подразделения")

    is_temporary: bool = Field(False, description="Флаг временного подразделения")
    start_date: Optional[date] = Field(None, description="Дата начала (для временных)")
    end_date: Optional[date] = Field(None, description="Дата окончания (для временных)")

    manager: Optional[OrgUnitManagerSchema] = Field(
        None, description="Руководитель подразделения"
    )
    children: List["OrgUnitHierarchySchema"] = Field(
        [], description="Список дочерних подразделений"
    )


OrgUnitHierarchySchema.model_rebuild()


class OrgUnitCreateSchema(BaseModel):
    name: str = Field(..., description="Название подразделения")
    unit_type: OrgUnitType = Field(..., description="Тип структурной единицы")
    parent_id: Optional[int] = Field(None, description="ID родительского подразделения")
    manager_eid: Optional[int] = Field(None, description="EID руководителя")
    is_temporary: bool = Field(False, description="Флаг временного подразделения")
    start_date: Optional[date] = Field(None, description="Дата начала (для временных)")
    end_date: Optional[date] = Field(None, description="Дата окончания (для временных)")


class OrgUnitUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, description="Название подразделения")
    unit_type: Optional[OrgUnitType] = Field(
        None, description="Тип структурной единицы"
    )
    is_temporary: Optional[bool] = Field(
        None, description="Флаг временного подразделения"
    )
    start_date: Optional[date] = Field(None, description="Дата начала (для временных)")
    end_date: Optional[date] = Field(None, description="Дата окончания (для временных)")

class OrgChangeLogShema(BaseModel):
    id: int = Field(...)
    org_unit_id: int = Field(...)
    changed_by_eid: int = Field(...)
    changed_at: datetime = Field(...)
    field_name: str = Field(...)

    old_value: Union[str, Dict[str, Any], List[Any], bool, int] | None = Field(
        None
    )
    new_value: Union[str, Dict[str, Any], List[Any], bool, int] | None = Field(
        None
    )

    operation: Any = Field(...)

    class Config:
        from_attributes = True