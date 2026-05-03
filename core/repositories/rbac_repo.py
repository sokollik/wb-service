from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.rbac import (
    CuratorScopeOrm,
    PermissionOrm,
    RoleEnum,
    RoleOrm,
    RolePermissionOrm,
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


    async def get_permissions_for_role_names(
        self, role_names: List[str]
    ) -> List[PermissionOrm]:
        if not role_names:
            return []

        query = (
            select(PermissionOrm)
            .join(RolePermissionOrm, PermissionOrm.id == RolePermissionOrm.permission_id)
            .join(RoleOrm, RoleOrm.id == RolePermissionOrm.role_id)
            .where(RoleOrm.name.in_(role_names))
        )
        result = await self.session.execute(query)
        return list({p.id: p for p in result.scalars().all()}.values())

    async def check_role_permission(
        self, role_names: List[str], resource: str, action: str
    ) -> bool:
        if not role_names:
            return False

        permission_name = f"{resource}:{action}"
        query = (
            select(PermissionOrm.id)
            .join(RolePermissionOrm, PermissionOrm.id == RolePermissionOrm.permission_id)
            .join(RoleOrm, RoleOrm.id == RolePermissionOrm.role_id)
            .where(
                RoleOrm.name.in_(role_names),
                PermissionOrm.name == permission_name,
            )
            .limit(1)
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
            (RoleEnum.EMPLOYEE.value, "Базовый сотрудник"),
            (RoleEnum.CURATOR.value, "Куратор с расширенными правами"),
            (RoleEnum.NEWS_EDITOR.value, "Редактор новостей"),
            (RoleEnum.HR.value, "Сотрудник HR"),
            (RoleEnum.ADMIN.value, "Администратор системы"),
        ]
        for role_name, description in roles_data:
            existing = await self.get_role_by_name(role_name)
            if not existing:
                await self.create_role(name=role_name, description=description)

        permissions_data = [
            ("news:read", "news", "read", "Чтение новостей"),
            ("news:create", "news", "create", "Создание новостей"),
            ("news:update", "news", "update", "Редактирование новостей"),
            ("news:delete", "news", "delete", "Удаление новостей"),
            ("news:manage", "news", "manage", "Управление категориями/логами/ack"),
            ("comments:create", "comments", "create", "Создание комментариев"),
            ("comments:read", "comments", "read", "Чтение комментариев"),
            ("comments:delete", "comments", "delete", "Удаление комментариев"),
            ("profile:read", "profile", "read", "Чтение профилей"),
            ("profile:update", "profile", "update", "Редактирование профилей"),
            ("profile:manage", "profile", "manage", "Управление профилями"),
            ("documents:read", "documents", "read", "Чтение документов"),
            ("documents:create", "documents", "create", "Загрузка документов"),
            ("documents:update", "documents", "update", "Редактирование документов"),
            ("documents:delete", "documents", "delete", "Удаление документов"),
            ("documents:manage", "documents", "manage", "Управление документами"),
            ("folders:manage", "folders", "manage", "Управление папками"),
            ("notifications:read", "notifications", "read", "Чтение уведомлений"),
            ("notifications:manage", "notifications", "manage", "Управление уведомлениями"),
            ("org:read", "org", "read", "Чтение оргструктуры"),
            ("org:manage", "org", "manage", "Управление оргструктурой"),
            ("rbac:manage", "rbac", "manage", "Управление RBAC"),
            ("integrations:manage", "integrations", "manage", "Управление интеграциями"),
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

        role_to_perms = {
            RoleEnum.EMPLOYEE.value: [
                "news:read",
                "comments:create",
                "comments:read",
                "profile:read",
                "documents:read",
                "documents:create",
                "notifications:read",
                "org:read",
            ],
            RoleEnum.CURATOR.value: [
                "news:read",
                "news:create",
                "news:update",
                "news:delete",
                "comments:create",
                "comments:read",
                "comments:delete",
                "profile:read",
                "documents:read",
                "documents:create",
                "documents:update",
                "documents:delete",
                "documents:manage",
                "notifications:read",
                "org:read",
            ],
            RoleEnum.NEWS_EDITOR.value: [
                "news:read",
                "news:create",
                "news:update",
                "news:delete",
                "comments:create",
                "comments:read",
                "profile:read",
                "documents:read",
                "notifications:read",
                "org:read",
            ],
            RoleEnum.HR.value: [
                "news:read",
                "comments:create",
                "comments:read",
                "profile:read",
                "profile:update",
                "profile:manage",
                "documents:read",
                "documents:create",
                "documents:update",
                "documents:delete",
                "documents:manage",
                "folders:manage",
                "notifications:read",
                "notifications:manage",
                "org:read",
                "org:manage",
            ],
            RoleEnum.ADMIN.value: None,  # все разрешения
        }

        for role_name, perm_names in role_to_perms.items():
            role = await self.get_role_by_name(role_name)
            if not role:
                continue
            if perm_names is None:
                perms = await self.get_all_permissions()
            else:
                perms = [
                    await self.get_permission_by_name(name) for name in perm_names
                ]
            for perm in perms:
                if perm:
                    await self.assign_permission_to_role(role.id, perm.id)
