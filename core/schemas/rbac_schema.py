from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from core.models.rbac import RoleEnum

class RoleBaseSchema(BaseModel):
    name: str = Field(..., description="Название роли (EMPLOYEE/CURATOR/ADMIN)")
    description: Optional[str] = Field(None, description="Описание роли")


class RoleCreateSchema(RoleBaseSchema):
    pass


class RoleUpdateSchema(BaseModel):
    description: Optional[str] = Field(None, description="Описание роли")


class RoleSchema(RoleBaseSchema):
    id: int = Field(..., description="ID роли")
    created_at: datetime = Field(..., description="Дата создания роли")

    model_config = ConfigDict(from_attributes=True)


class RoleWithPermissionsSchema(RoleSchema):
    permissions: List["PermissionSchema"] = Field(
        default_factory=list,
        description="Список разрешений роли"
    )

class PermissionBaseSchema(BaseModel):
    name: str = Field(..., description="Уникальное имя разрешения (news:create)")
    resource: str = Field(..., description="Ресурс (news, comments, profile)")
    action: str = Field(..., description="Действие (create, read, update, delete)")
    description: Optional[str] = Field(None, description="Описание разрешения")


class PermissionCreateSchema(PermissionBaseSchema):
    pass


class PermissionUpdateSchema(BaseModel):
    description: Optional[str] = Field(None, description="Описание разрешения")


class PermissionSchema(PermissionBaseSchema):
    id: int = Field(..., description="ID разрешения")

    model_config = ConfigDict(from_attributes=True)


class RolePermissionCreateSchema(BaseModel):
    role_id: int = Field(..., description="ID роли")
    permission_id: int = Field(..., description="ID разрешения")


class RolePermissionSchema(BaseModel):
    role_id: int = Field(..., description="ID роли")
    permission_id: int = Field(..., description="ID разрешения")

    model_config = ConfigDict(from_attributes=True)


class UserRoleCreateSchema(BaseModel):
    user_eid: str = Field(..., description="EID пользователя")
    role_id: int = Field(..., description="ID роли")
    granted_by: Optional[str] = Field(None, description="EID выдавшего роль")


class UserRoleSchema(BaseModel):
    user_eid: str = Field(..., description="EID пользователя")
    role_id: int = Field(..., description="ID роли")
    granted_by: Optional[str] = Field(None, description="EID выдавшего роль")
    granted_at: datetime = Field(..., description="Дата выдачи роли")

    model_config = ConfigDict(from_attributes=True)


class UserRolesResponseSchema(BaseModel):
    user_eid: str = Field(..., description="EID пользователя")
    roles: List[RoleSchema] = Field(
        default_factory=list,
        description="Список ролей пользователя"
    )

class CuratorScopeCreateSchema(BaseModel):
    curator_eid: str = Field(..., description="EID куратора")
    org_unit_id: int = Field(..., description="ID подразделения")


class CuratorScopeSchema(BaseModel):
    id: int = Field(..., description="ID записи scope")
    curator_eid: str = Field(..., description="EID куратора")
    org_unit_id: int = Field(..., description="ID подразделения")

    model_config = ConfigDict(from_attributes=True)


class CuratorScopeWithOrgUnitSchema(CuratorScopeSchema):
    org_unit_name: str = Field(..., description="Название подразделения")
    org_unit_type: str = Field(..., description="Тип подразделения")

class PermissionCheckSchema(BaseModel):
    resource: str = Field(..., description="Ресурс")
    action: str = Field(..., description="Действие")

class ScopeCheckSchema(BaseModel):
    org_unit_id: int = Field(..., description="ID подразделения для проверки")

class RBACUserDetailSchema(BaseModel):
    user_eid: str = Field(..., description="EID пользователя")
    roles: List[RoleWithPermissionsSchema] = Field(
        default_factory=list,
        description="Список ролей с разрешениями"
    )
    curator_scopes: List[CuratorScopeWithOrgUnitSchema] = Field(
        default_factory=list,
        description="Список подразделений, доступных куратору"
    )
    all_permissions: List[str] = Field(
        default_factory=list,
        description="Все уникальные разрешения пользователя"
    )

RoleWithPermissionsSchema.model_rebuild()
