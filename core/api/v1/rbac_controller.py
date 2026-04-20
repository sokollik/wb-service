from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from fastapi_restful.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession
from core.api.deps import CurrentUser, require_roles, get_rbac_service
from core.schemas.rbac_schema import (
    CuratorScopeSchema,
    PermissionCreateSchema,
    PermissionSchema,
    RBACUserDetailSchema,
    RoleCreateSchema,
    RoleSchema,
    RoleUpdateSchema,
    RoleWithPermissionsSchema,
    UserRolesResponseSchema,
)
from core.services.rbac_service import RBACService
from core.utils.common_util import exception_handler
from core.utils.db_util import get_session_obj

rbac_router = APIRouter(prefix="/rbac", tags=["RBAC"])


@cbv(rbac_router)
class RBACController:
    def __init__(
        self,
        session: AsyncSession = Depends(get_session_obj),
        rbac_service: RBACService = Depends(get_rbac_service),
    ):
        self.session = session
        self.rbac_service = rbac_service

    @rbac_router.get("/roles", response_model=List[RoleSchema])
    @exception_handler
    async def get_all_roles(
        self,
        _current_user: CurrentUser = Depends(
            require_roles(["admin"])
        ),
    ):
        return await self.rbac_service.get_all_roles()

    @rbac_router.get("/roles/{role_id}", response_model=RoleSchema)
    @exception_handler
    async def get_role(
        self,
        role_id: int,
        _current_user: CurrentUser = Depends(
            require_roles(["admin", "curator"])
        ),
    ):
        return await self.rbac_service.get_role(role_id)

    @rbac_router.post("/roles", response_model=RoleSchema)
    @exception_handler
    async def create_role(
        self,
        data: RoleCreateSchema,
        _current_user: CurrentUser = Depends(require_roles(["admin"])),
    ):
        return await self.rbac_service.create_role(
            name=data.name, description=data.description
        )

    @rbac_router.put("/roles/{role_id}", response_model=RoleSchema)
    @exception_handler
    async def update_role(
        self,
        role_id: int,
        data: RoleUpdateSchema,
        _current_user: CurrentUser = Depends(require_roles(["admin"])),
    ):
        return await self.rbac_service.update_role(
            role_id=role_id, description=data.description
        )

    @rbac_router.delete("/roles/{role_id}")
    @exception_handler
    async def delete_role(
        self,
        role_id: int,
        _current_user: CurrentUser = Depends(require_roles(["admin"])),
    ):
        return await self.rbac_service.delete_role(role_id)

    @rbac_router.get("/permissions", response_model=List[PermissionSchema])
    @exception_handler
    async def get_all_permissions(
        self,
        _current_user: CurrentUser = Depends(
            require_roles(["admin", "curator"])
        ),
    ):
        return await self.rbac_service.get_all_permissions()

    @rbac_router.get(
        "/permissions/resource/{resource}",
        response_model=List[PermissionSchema],
    )
    @exception_handler
    async def get_permissions_by_resource(
        self,
        resource: str,
        _current_user: CurrentUser = Depends(
            require_roles(["admin", "curator"])
        ),
    ):
        return await self.rbac_service.get_permissions_by_resource(resource)

    @rbac_router.post("/permissions", response_model=PermissionSchema)
    @exception_handler
    async def create_permission(
        self,
        data: PermissionCreateSchema,
        _current_user: CurrentUser = Depends(require_roles(["admin"])),
    ):
        return await self.rbac_service.create_permission(
            name=data.name,
            resource=data.resource,
            action=data.action,
            description=data.description,
        )

    @rbac_router.delete("/permissions/{permission_id}")
    @exception_handler
    async def delete_permission(
        self,
        permission_id: int,
        _current_user: CurrentUser = Depends(require_roles(["admin"])),
    ):
        return await self.rbac_service.delete_permission(permission_id)

    @rbac_router.get(
        "/roles/{role_id}/permissions",
        response_model=List[PermissionSchema],
    )
    @exception_handler
    async def get_role_permissions(
        self,
        role_id: int,
        _current_user: CurrentUser = Depends(
            require_roles(["admin", "curator"])
        ),
    ):
        return await self.rbac_service.get_role_permissions(role_id)

    @rbac_router.post("/roles/{role_id}/permissions/{permission_id}")
    @exception_handler
    async def assign_permission_to_role(
        self,
        role_id: int,
        permission_id: int,
        _current_user: CurrentUser = Depends(require_roles(["admin"])),
    ):
        return await self.rbac_service.assign_permission_to_role(
            role_id=role_id, permission_id=permission_id
        )

    @rbac_router.delete("/roles/{role_id}/permissions/{permission_id}")
    @exception_handler
    async def remove_permission_from_role(
        self,
        role_id: int,
        permission_id: int,
        _current_user: CurrentUser = Depends(require_roles(["admin"])),
    ):
        return await self.rbac_service.remove_permission_from_role(
            role_id=role_id, permission_id=permission_id
        )

    @rbac_router.get("/users/{user_eid}/roles", response_model=UserRolesResponseSchema)
    @exception_handler
    async def get_user_roles(
        self,
        user_eid: str,
        _current_user: CurrentUser = Depends(
            require_roles(["admin", "hr"])
        ),
    ):
        return await self.rbac_service.get_user_roles(user_eid)

    @rbac_router.post("/users/{user_eid}/roles/{role_id}")
    @exception_handler
    async def assign_role_to_user(
        self,
        user_eid: str,
        role_id: int,
        current_user: CurrentUser = Depends(require_roles(["admin", "hr"])),
    ):
        return await self.rbac_service.assign_role_to_user(
            user_eid=user_eid,
            role_id=role_id,
            granted_by=current_user.eid,
        )

    @rbac_router.delete("/users/{user_eid}/roles/{role_id}")
    @exception_handler
    async def remove_role_from_user(
        self,
        user_eid: str,
        role_id: int,
        _current_user: CurrentUser = Depends(require_roles(["admin", "hr"])),
    ):
        return await self.rbac_service.remove_role_from_user(
            user_eid=user_eid, role_id=role_id
        )

    @rbac_router.delete("/users/{user_eid}/roles")
    @exception_handler
    async def remove_all_roles_from_user(
        self,
        user_eid: str,
        _current_user: CurrentUser = Depends(require_roles(["admin", "hr"])),
    ):
        return await self.rbac_service.remove_all_roles_from_user(user_eid)

    @rbac_router.get(
        "/curators/{curator_eid}/scopes",
        response_model=List[CuratorScopeSchema],
    )
    @exception_handler
    async def get_curator_scopes(
        self,
        curator_eid: str,
        _current_user: CurrentUser = Depends(
            require_roles(["admin", "hr", "curator"])
        ),
    ):
        return await self.rbac_service.get_curator_scopes(curator_eid)

    @rbac_router.post("/curators/{curator_eid}/scopes/{org_unit_id}")
    @exception_handler
    async def add_curator_scope(
        self,
        curator_eid: str,
        org_unit_id: int,
        _current_user: CurrentUser = Depends(require_roles(["admin", "hr"])),
    ):
        return await self.rbac_service.add_curator_scope(
            curator_eid=curator_eid, org_unit_id=org_unit_id
        )

    @rbac_router.delete("/curators/{curator_eid}/scopes/{org_unit_id}")
    @exception_handler
    async def remove_curator_scope(
        self,
        curator_eid: str,
        org_unit_id: int,
        _current_user: CurrentUser = Depends(require_roles(["admin", "hr"])),
    ):
        return await self.rbac_service.remove_curator_scope(
            curator_eid=curator_eid, org_unit_id=org_unit_id
        )

    @rbac_router.get("/users/{user_eid}/detail", response_model=RBACUserDetailSchema)
    @exception_handler
    async def get_user_detail(
        self,
        user_eid: str,
        _current_user: CurrentUser = Depends(
            require_roles(["admin", "hr"])
        ),
    ):
        return await self.rbac_service.get_user_detail(user_eid)

    @rbac_router.post("/initialize")
    @exception_handler
    async def initialize_default_data(
        self,
        _current_user: CurrentUser = Depends(require_roles(["admin"])),
    ):
        """Инициализировать дефолтные роли и разрешения (только admin)"""
        await self.rbac_service.initialize_default_data()
        return {"message": "Дефолтные роли и разрешения созданы"}
