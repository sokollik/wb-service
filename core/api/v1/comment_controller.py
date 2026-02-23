from typing import Literal

from fastapi import APIRouter, Depends
from fastapi_restful.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession

from core.api.deps import CurrentUser, require_roles
from core.schemas.comment_schema import (
    CommentCreateSchema,
    CommentUpdateSchema,
    CommentViewSchema,
)
from core.services.comment_service import CommentService
from core.utils.common_util import exception_handler
from core.utils.db_util import get_session_obj

comment_controller = APIRouter()


@cbv(comment_controller)
class CommentController:

    def __init__(
        self,
        session: AsyncSession = Depends(get_session_obj),
    ):
        self.session = session
        self.comment_service = CommentService(session=session)

    @comment_controller.get("/")
    @exception_handler
    async def view_comments(
        self,
        news_id: int,
        sort_by: Literal["popular", "new"] = "new",
        current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
    ) -> CommentViewSchema:
        return await self.comment_service.get_comments(
            news_id=news_id, sort_by=sort_by, user_eid=current_user.eid
        )

    @comment_controller.post("/")
    @exception_handler
    async def create_comment(
        self,
        comment: CommentCreateSchema,
        current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
    ) -> int:
        new_comment_id = await self.comment_service.create_comment(
            comment=comment, author_eid=current_user.eid
        )
        return new_comment_id

    @comment_controller.put("/")
    @exception_handler
    async def edit_comment(
        self,
        comment: CommentUpdateSchema,
        current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
    ):
        await self.comment_service.edit_comment(
            comment=comment, editor_eid=current_user.eid
        )

    @comment_controller.delete("/")
    @exception_handler
    async def delete_comment(
        self,
        comment_id: int,
        current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
    ):
        await self.comment_service.delete_comment(
            comment_id=comment_id, eid=current_user.eid, roles=current_user.roles
        )

    @comment_controller.post("/like/add")
    @exception_handler
    async def add_like(
        self,
        comment_id: int,
        current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
    ):
        await self.comment_service.add_like(
            comment_id=comment_id, eid=current_user.eid
        )

    @comment_controller.delete("/like/remove")
    @exception_handler
    async def remove_like(
        self,
        comment_id: int,
        current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
    ):
        await self.comment_service.remove_like(
            comment_id=comment_id, eid=current_user.eid
        )

    @comment_controller.get("/{comment_id}/log")
    @exception_handler
    async def get_comment_edit_log(
        self,
        comment_id: int,
        current_user: CurrentUser = Depends(require_roles(["admin"])),
    ):
        return await self.comment_service.get_comment_edit_log(
            comment_id=comment_id
        )
