from typing import List, Optional
from sqlalchemy import delete, exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from core.models.rbac import (
    CuratorScopeOrm,
    PermissionOrm,
    RoleEnum,
    RoleOrm,
    RolePermissionOrm,
    UserRoleOrm,
)

class RBACRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_role_by_name(self, name: str) -> Optional[RoleOrm]:
        query = select(RoleOrm).where(RoleOrm.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_role_by_id(self, role_id: int) -> Optional[RoleOrm]:
        return await self.session.get(RoleOrm, role_id)

    async def get_all_roles(self) -> List[RoleOrm]:
        query = select(RoleOrm).order_by(RoleOrm.name)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create_role(
        self, name: str, description: Optional[str] = None
    ) -> RoleOrm:
        
        role = RoleOrm(name=name, description=description)
        self.session.add(role)
        await self.session.flush()
        return role

    async def update_role(
        self, role_id: int, description: Optional[str] = None
    ) -> Optional[RoleOrm]:

        role = await self.get_role_by_id(role_id)
        if role:
            if description is not None:
                role.description = description
            await self.session.flush()
        return role

    async def delete_role(self, role_id: int) -> bool:

        result = await self.session.execute(
            delete(RoleOrm).where(RoleOrm.id == role_id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def get_permission_by_name(
        self, name: str
    ) -> Optional[PermissionOrm]:

        query = select(PermissionOrm).where(PermissionOrm.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_permission_by_id(
        self, permission_id: int
    ) -> Optional[PermissionOrm]:

        return await self.session.get(PermissionOrm, permission_id)

    async def get_all_permissions(self) -> List[PermissionOrm]:

        query = select(PermissionOrm).order_by(PermissionOrm.name)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_permissions_by_resource(
        self, resource: str
    ) -> List[PermissionOrm]:

        query = select(PermissionOrm).where(PermissionOrm.resource == resource)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create_permission(
        self,
        name: str,
        resource: str,
        action: str,
        description: Optional[str] = None,
    ) -> PermissionOrm:

        permission = PermissionOrm(
            name=name, resource=resource, action=action, description=description
        )
        self.session.add(permission)
        await self.session.flush()
        return permission

    async def delete_permission(self, permission_id: int) -> bool:

        result = await self.session.execute(
            delete(PermissionOrm).where(PermissionOrm.id == permission_id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def assign_permission_to_role(
        self, role_id: int, permission_id: int
    ) -> bool:
        exists_query = select(RolePermissionOrm).where(
            RolePermissionOrm.role_id == role_id,
            RolePermissionOrm.permission_id == permission_id,
        )
        result = await self.session.execute(exists_query)
        if result.scalar_one_or_none():
            return False

        role_permission = RolePermissionOrm(
            role_id=role_id, permission_id=permission_id
        )
        self.session.add(role_permission)
        await self.session.flush()
        return True

    async def remove_permission_from_role(
        self, role_id: int, permission_id: int
    ) -> bool:
        result = await self.session.execute(
            delete(RolePermissionOrm).where(
                RolePermissionOrm.role_id == role_id,
                RolePermissionOrm.permission_id == permission_id,
            )
        )
        await self.session.flush()
        return result.rowcount > 0

    async def get_role_permissions(self, role_id: int) -> List[PermissionOrm]:
        query = (
            select(PermissionOrm)
            .join(RolePermissionOrm, PermissionOrm.id == RolePermissionOrm.permission_id)
            .where(RolePermissionOrm.role_id == role_id)
        )
        result = await self.session.execute(query)
        return result.scalars().all()


    async def get_user_roles(self, user_eid: str) -> List[RoleOrm]:
        query = (
            select(RoleOrm)
            .join(UserRoleOrm, RoleOrm.id == UserRoleOrm.role_id)
            .where(UserRoleOrm.user_eid == user_eid)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def assign_role_to_user(
        self, user_eid: str, role_id: int, granted_by: Optional[str] = None
    ) -> bool:

        exists_query = select(UserRoleOrm).where(
            UserRoleOrm.user_eid == user_eid,
            UserRoleOrm.role_id == role_id,
        )
        result = await self.session.execute(exists_query)
        if result.scalar_one_or_none():
            return False

        user_role = UserRoleOrm(
            user_eid=user_eid, role_id=role_id, granted_by=granted_by
        )
        self.session.add(user_role)
        await self.session.flush()
        return True

    async def remove_role_from_user(
        self, user_eid: str, role_id: int
    ) -> bool:

        result = await self.session.execute(
            delete(UserRoleOrm).where(
                UserRoleOrm.user_eid == user_eid,
                UserRoleOrm.role_id == role_id,
            )
        )
        await self.session.flush()
        return result.rowcount > 0

    async def remove_all_roles_from_user(self, user_eid: str) -> int:

        result = await self.session.execute(
            delete(UserRoleOrm).where(UserRoleOrm.user_eid == user_eid)
        )
        await self.session.flush()
        return result.rowcount
    
    async def get_user_permissions(self, user_eid: str) -> List[PermissionOrm]:

        query = (
            select(PermissionOrm)
            .join(RolePermissionOrm, PermissionOrm.id == RolePermissionOrm.permission_id)
            .join(UserRoleOrm, RoleOrm.id == UserRoleOrm.role_id)
            .where(UserRoleOrm.user_eid == user_eid)
        )
        result = await self.session.execute(query)
        return list({p.id: p for p in result.scalars().all()}.values())

    async def check_user_permission(
        self, user_eid: str, resource: str, action: str
    ) -> bool:
        permission_name = f"{resource}:{action}"
        
        query = (
            select(PermissionOrm)
            .join(RolePermissionOrm, PermissionOrm.id == RolePermissionOrm.permission_id)
            .join(UserRoleOrm, RoleOrm.id == UserRoleOrm.role_id)
            .where(
                UserRoleOrm.user_eid == user_eid,
                PermissionOrm.name == permission_name,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def check_user_role(
        self, user_eid: str, required_roles: List[str]
    ) -> bool:
        query = (
            select(RoleOrm)
            .join(UserRoleOrm, RoleOrm.id == UserRoleOrm.role_id)
            .where(
                UserRoleOrm.user_eid == user_eid,
                RoleOrm.name.in_(required_roles),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_curator_scopes(self, curator_eid: str) -> List[CuratorScopeOrm]:
        query = select(CuratorScopeOrm).where(
            CuratorScopeOrm.curator_eid == curator_eid
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def add_curator_scope(
        self, curator_eid: str, org_unit_id: int
    ) -> bool:

        exists_query = select(CuratorScopeOrm).where(
            CuratorScopeOrm.curator_eid == curator_eid,
            CuratorScopeOrm.org_unit_id == org_unit_id,
        )
        result = await self.session.execute(exists_query)
        if result.scalar_one_or_none():
            return False

        scope = CuratorScopeOrm(
            curator_eid=curator_eid, org_unit_id=org_unit_id
        )
        self.session.add(scope)
        await self.session.flush()
        return True

    async def remove_curator_scope(
        self, curator_eid: str, org_unit_id: int
    ) -> bool:
        result = await self.session.execute(
            delete(CuratorScopeOrm).where(
                CuratorScopeOrm.curator_eid == curator_eid,
                CuratorScopeOrm.org_unit_id == org_unit_id,
            )
        )
        await self.session.flush()
        return result.rowcount > 0

    async def check_curator_scope(
        self, curator_eid: str, org_unit_id: int
    ) -> bool:

        query = select(CuratorScopeOrm).where(
            CuratorScopeOrm.curator_eid == curator_eid,
            CuratorScopeOrm.org_unit_id == org_unit_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_curators_for_org_unit(
        self, org_unit_id: int
    ) -> List[str]:

        query = select(CuratorScopeOrm.curator_eid).where(
            CuratorScopeOrm.org_unit_id == org_unit_id
        )
        result = await self.session.execute(query)
        return [row[0] for row in result.all()]

    async def get_org_units_for_curator(
        self, curator_eid: str
    ) -> List[int]:

        query = select(CuratorScopeOrm.org_unit_id).where(
            CuratorScopeOrm.curator_eid == curator_eid
        )
        result = await self.session.execute(query)
        return [row[0] for row in result.all()]

    async def initialize_default_roles(self):

        roles_data = [
            (RoleEnum.EMPLOYEE, "Базовый сотрудник"),
            (RoleEnum.CURATOR, "Куратор с расширенными правами"),
            (RoleEnum.ADMIN, "Администратор системы"),
        ]

        for role_name, description in roles_data:
            existing = await self.get_role_by_name(role_name)
            if not existing:
                await self.create_role(name=role_name, description=description)

        permissions_data = [
            ("news:create", "news", "create", "Создание новостей"),
            ("news:read", "news", "read", "Чтение новостей"),
            ("news:update", "news", "update", "Редактирование новостей"),
            ("news:delete", "news", "delete", "Удаление новостей"),
            ("news:publish", "news", "publish", "Публикация новостей"),
            ("comments:create", "comments", "create", "Создание комментариев"),
            ("comments:read", "comments", "read", "Чтение комментариев"),
            ("comments:delete", "comments", "delete", "Удаление комментариев"),
            ("profile:read", "profile", "read", "Чтение профилей"),
            ("profile:update", "profile", "update", "Редактирование профилей"),
            ("documents:create", "documents", "create", "Загрузка документов"),
            ("documents:read", "documents", "read", "Чтение документов"),
            ("documents:delete", "documents", "delete", "Удаление документов"),
            ("users:manage", "users", "manage", "Управление пользователями"),
            ("roles:manage", "roles", "manage", "Управление ролями"),
            ("permissions:manage", "permissions", "manage", "Управление разрешениями"),
        ]

        for perm_name, resource, action, description in permissions_data:
            existing = await self.get_permission_by_name(perm_name)
            if not existing:
                await self.create_permission(
                    name=perm_name,
                    resource=resource,
                    action=action,
                    description=description,
                )

        employee_role = await self.get_role_by_name(RoleEnum.EMPLOYEE)
        curator_role = await self.get_role_by_name(RoleEnum.CURATOR)
        admin_role = await self.get_role_by_name(RoleEnum.ADMIN)

        if employee_role:
            for perm_name in [
                "news:read",
                "comments:create",
                "comments:read",
                "profile:read",
                "documents:read",
            ]:
                perm = await self.get_permission_by_name(perm_name)
                if perm:
                    await self.assign_permission_to_role(
                        employee_role.id, perm.id
                    )

        if curator_role:
            for perm_name in [
                "news:read",
                "news:create",
                "news:update",
                "comments:create",
                "comments:read",
                "comments:delete",
                "profile:read",
                "documents:create",
                "documents:read",
                "documents:delete",
            ]:
                perm = await self.get_permission_by_name(perm_name)
                if perm:
                    await self.assign_permission_to_role(
                        curator_role.id, perm.id
                    )

        if admin_role:
            all_perms = await self.get_all_permissions()
            for perm in all_perms:
                await self.assign_permission_to_role(admin_role.id, perm.id)
