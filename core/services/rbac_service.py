from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.common.common_exc import ForbiddenHttpException, NotFoundException
from core.config.settings import get_settings
from core.models.rbac import RoleEnum
from core.models.org_structure import OrgUnitOrm
from core.repositories.rbac_repo import RBACRepository
from core.schemas.rbac_schema import (
    CuratorScopeSchema,
    PermissionSchema,
    RBACUserDetailSchema,
    RoleSchema,
    RoleWithPermissionsSchema,
    UserRolesResponseSchema,
)

class RBACService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.rbac_repo = RBACRepository(session=self.session)
        self.settings = get_settings()

    async def get_all_roles(self) -> List[RoleSchema]:
        roles = await self.rbac_repo.get_all_roles()
        return [RoleSchema.model_validate(role) for role in roles]

    async def get_role(self, role_id: int) -> RoleSchema:
        role = await self.rbac_repo.get_role_by_id(role_id)
        if not role:
            raise NotFoundException(name="role", id=role_id)
        return RoleSchema.model_validate(role)

    async def create_role(
        self, name: str, description: Optional[str] = None
    ) -> RoleSchema:
        existing = await self.rbac_repo.get_role_by_name(name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Роль с названием '{name}' уже существует",
            )
        role = await self.rbac_repo.create_role(
            name=name, description=description
        )
        return RoleSchema.model_validate(role)

    async def update_role(
        self, role_id: int, description: Optional[str] = None
    ) -> RoleSchema:
        role = await self.rbac_repo.update_role(
            role_id=role_id, description=description
        )
        if not role:
            raise NotFoundException(name="role", id=role_id)
        return RoleSchema.model_validate(role)

    async def delete_role(self, role_id: int) -> bool:
        return await self.rbac_repo.delete_role(role_id)

    async def get_all_permissions(self) -> List[PermissionSchema]:
        permissions = await self.rbac_repo.get_all_permissions()
        return [PermissionSchema.model_validate(p) for p in permissions]

    async def get_permissions_by_resource(
        self, resource: str
    ) -> List[PermissionSchema]:
        permissions = await self.rbac_repo.get_permissions_by_resource(resource)
        return [PermissionSchema.model_validate(p) for p in permissions]

    async def create_permission(
        self,
        name: str,
        resource: str,
        action: str,
        description: Optional[str] = None,
    ) -> PermissionSchema:

        existing = await self.rbac_repo.get_permission_by_name(name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Разрешение '{name}' уже существует",
            )
        permission = await self.rbac_repo.create_permission(
            name=name, resource=resource, action=action, description=description
        )
        return PermissionSchema.model_validate(permission)

    async def delete_permission(self, permission_id: int) -> bool:
        return await self.rbac_repo.delete_permission(permission_id)


    async def assign_permission_to_role(
        self, role_id: int, permission_id: int
    ) -> bool:
        role = await self.rbac_repo.get_role_by_id(role_id)
        if not role:
            raise NotFoundException(name="role", id=role_id)

        permission = await self.rbac_repo.get_permission_by_id(permission_id)
        if not permission:
            raise NotFoundException(name="permission", id=permission_id)

        return await self.rbac_repo.assign_permission_to_role(
            role_id=role_id, permission_id=permission_id
        )

    async def remove_permission_from_role(
        self, role_id: int, permission_id: int
    ) -> bool:
        return await self.rbac_repo.remove_permission_from_role(
            role_id=role_id, permission_id=permission_id
        )

    async def get_role_permissions(self, role_id: int) -> List[PermissionSchema]:
        permissions = await self.rbac_repo.get_role_permissions(role_id)
        return [PermissionSchema.model_validate(p) for p in permissions]

    async def get_user_roles(self, user_eid: str) -> UserRolesResponseSchema:
        roles = await self.rbac_repo.get_user_roles(user_eid)
        return UserRolesResponseSchema(
            user_eid=user_eid,
            roles=[RoleSchema.model_validate(role) for role in roles],
        )

    async def assign_role_to_user(
        self, user_eid: str, role_id: int, granted_by: Optional[str] = None
    ) -> bool:
        role = await self.rbac_repo.get_role_by_id(role_id)
        if not role:
            raise NotFoundException(name="role", id=role_id)

        return await self.rbac_repo.assign_role_to_user(
            user_eid=user_eid, role_id=role_id, granted_by=granted_by
        )

    async def remove_role_from_user(
        self, user_eid: str, role_id: int
    ) -> bool:
        return await self.rbac_repo.remove_role_from_user(
            user_eid=user_eid, role_id=role_id
        )

    async def remove_all_roles_from_user(self, user_eid: str) -> int:
        return await self.rbac_repo.remove_all_roles_from_user(user_eid)

    async def check_permission(
        self, user_eid: str, resource: str, action: str
    ) -> bool:
 
        return await self.rbac_repo.check_user_permission(
            user_eid=user_eid, resource=resource, action=action
        )

    async def check_role(
        self, user_eid: str, required_roles: List[str]
    ) -> bool:

        return await self.rbac_repo.check_user_role(
            user_eid=user_eid, required_roles=required_roles
        )

    async def check_role_or_permission(
        self,
        user_eid: str,
        required_roles: Optional[List[str]] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
    ) -> bool:
        if required_roles and await self.check_role(user_eid, required_roles):
            return True

        if resource and action and await self.check_permission(
            user_eid, resource, action
        ):
            return True

        return False

    async def enforce_permission(
        self,
        user_eid: str,
        resource: str,
        action: str,
        required_roles: Optional[List[str]] = None,
    ):
        # Skip RBAC check in development if DISABLE_RBAC is true
        if self.settings.DISABLE_RBAC:
            return

        try:
            if await self.check_role(user_eid, [RoleEnum.ADMIN]):
                return

            if required_roles and await self.check_role(user_eid, required_roles):
                return
            has_permission = await self.check_permission(
                user_eid, resource, action
            )
            if not has_permission:
                raise ForbiddenHttpException(
                    detail=f"Недостаточно прав для {action} {resource}"
                )
        except Exception as e:
            # If RBAC tables don't exist or are empty, allow access in development
            if self.settings.DISABLE_RBAC or "does not exist" in str(e).lower() or "relation" in str(e).lower():
                return
            raise

    async def get_curator_scopes(
        self, curator_eid: str
    ) -> List[CuratorScopeSchema]:
        scopes = await self.rbac_repo.get_curator_scopes(curator_eid)
        return [CuratorScopeSchema.model_validate(s) for s in scopes]

    async def add_curator_scope(
        self, curator_eid: str, org_unit_id: int
    ) -> CuratorScopeSchema:
        from core.models.emploee import EmployeeOrm
        from sqlalchemy import select

        employee = await self.session.get(EmployeeOrm, curator_eid)
        if not employee:
            raise NotFoundException(name="employee", id=curator_eid)

        from core.models.org_structure import OrgUnitOrm

        org_unit = await self.session.get(OrgUnitOrm, org_unit_id)
        if not org_unit:
            raise NotFoundException(name="organization_unit", id=org_unit_id)

        success = await self.rbac_repo.add_curator_scope(
            curator_eid=curator_eid, org_unit_id=org_unit_id
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Такой scope уже существует",
            )

        return CuratorScopeSchema(
            curator_eid=curator_eid, org_unit_id=org_unit_id
        )

    async def remove_curator_scope(
        self, curator_eid: str, org_unit_id: int
    ) -> bool:
        return await self.rbac_repo.remove_curator_scope(
            curator_eid=curator_eid, org_unit_id=org_unit_id
        )

    async def check_scope(
        self, curator_eid: str, org_unit_id: int
    ) -> bool:
        if await self.check_role(curator_eid, [RoleEnum.ADMIN]):
            return True

        return await self.rbac_repo.check_curator_scope(
            curator_eid=curator_eid, org_unit_id=org_unit_id
        )

    async def check_scope_or_owner(
        self,
        user_eid: str,
        org_unit_id: int,
        owner_eid: Optional[str] = None,
    ) -> bool:

        if await self.check_role(user_eid, [RoleEnum.ADMIN]):
            return True

        if owner_eid and user_eid == owner_eid:
            return True

        return await self.check_scope(user_eid, org_unit_id)

    async def enforce_scope(
        self,
        curator_eid: str,
        org_unit_id: int,
        owner_eid: Optional[str] = None,
    ):
        has_access = await self.check_scope_or_owner(
            user_eid=curator_eid,
            org_unit_id=org_unit_id,
            owner_eid=owner_eid,
        )
        if not has_access:
            raise ForbiddenHttpException(
                detail="Нет доступа к этому подразделению"
            )

    async def get_user_detail(self, user_eid: str) -> RBACUserDetailSchema:
        roles = await self.rbac_repo.get_user_roles(user_eid)
        scopes = await self.rbac_repo.get_curator_scopes(user_eid)
        permissions = await self.rbac_repo.get_user_permissions(user_eid)

        roles_with_perms = []
        for role in roles:
            role_perms = await self.rbac_repo.get_role_permissions(role.id)
            roles_with_perms.append(
                RoleWithPermissionsSchema(
                    id=role.id,
                    name=role.name,
                    description=role.description,
                    created_at=role.created_at,
                    permissions=[
                        PermissionSchema.model_validate(p)
                        for p in role_perms
                    ],
                )
            )

        scopes_with_orgs = []
        for scope in scopes:
            org_unit = await self.session.get(OrgUnitOrm, scope.org_unit_id)
            if org_unit:
                scopes_with_orgs.append(
                    CuratorScopeSchema(
                        id=scope.id,
                        curator_eid=scope.curator_eid,
                        org_unit_id=scope.org_unit_id,
                    )
                )
        all_perms = list({p.name for p in permissions})

        return RBACUserDetailSchema(
            user_eid=user_eid,
            roles=roles_with_perms,
            curator_scopes=scopes_with_orgs,
            all_permissions=all_perms,
        )

    async def initialize_default_data(self):
        await self.rbac_repo.initialize_default_roles()
