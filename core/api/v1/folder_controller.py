from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi_restful.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession

from core.api.deps import CurrentUser, require_roles
from core.schemas.folder_schema import (
    FolderCreateSchema,
    FolderSchema,
    FolderTreeSchema,
    FolderUpdateSchema,
)
from core.services.folder_service import FolderService
from core.utils.common_util import exception_handler
from core.utils.db_util import get_session_obj

folder_router = APIRouter(tags=["Folders"])


@cbv(folder_router)
class FolderController:
    def __init__(self, session: AsyncSession = Depends(get_session_obj)):
        self.session = session
        self.folder_service = FolderService(session=session)

    @folder_router.get("/", response_model=List[FolderSchema])
    @exception_handler
    async def get_children(
        self,
        _current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin"])
        ),
        parent_id: Optional[int] = Query(None),
    ):
        return await self.folder_service.get_children(parent_id)

    @folder_router.get("/tree", response_model=List[FolderTreeSchema])
    @exception_handler
    async def get_tree(
        self,
        _current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin"])
        ),
        root_id: Optional[int] = Query(None),
    ):
        return await self.folder_service.get_tree(root_id)

    @folder_router.get("/{folder_id}", response_model=FolderSchema)
    @exception_handler
    async def get_folder(
        self,
        folder_id: int,
        _current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin"])
        ),
    ):
        return await self.folder_service.get_folder(folder_id)

    @folder_router.post("/", response_model=int)
    @exception_handler
    async def create_folder(
        self,
        data: FolderCreateSchema,
        current_user: CurrentUser = Depends(require_roles(["hr", "admin"])),
    ):
        return await self.folder_service.create_folder(
            data=data, created_by=current_user.eid
        )

    @folder_router.patch("/{folder_id}", response_model=FolderSchema)
    @exception_handler
    async def update_folder(
        self,
        folder_id: int,
        data: FolderUpdateSchema,
        _current_user: CurrentUser = Depends(require_roles(["hr", "admin"])),
    ):
        return await self.folder_service.update_folder(folder_id, data)

    @folder_router.delete("/{folder_id}")
    @exception_handler
    async def delete_folder(
        self,
        folder_id: int,
        _current_user: CurrentUser = Depends(require_roles(["hr", "admin"])),
    ):
        await self.folder_service.delete_folder(folder_id)
