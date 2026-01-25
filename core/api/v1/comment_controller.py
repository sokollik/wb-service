from typing import Literal

from fastapi import APIRouter, Depends
from fastapi_restful.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession

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
        self, news_id: int, sort_by: Literal["popular", "new"] = "new"
    ) -> CommentViewSchema:
        return await self.comment_service.get_comments(
            news_id=news_id, sort_by=sort_by
        )

    @comment_controller.post("/")
    @exception_handler
    async def create_comment(self, comment: CommentCreateSchema) -> int:
        new_comment_id = await self.comment_service.create_comment(
            comment=comment
        )
        return new_comment_id

    @comment_controller.put("/")
    @exception_handler
    async def edit_comment(self, comment: CommentUpdateSchema):
        await self.comment_service.edit_comment(comment=comment)

    @comment_controller.delete("/")
    @exception_handler
    async def delete_comment(self, comment_id: int, eid: int):
        await self.comment_service.delete_comment(
            comment_id=comment_id, eid=eid
        )

    @comment_controller.post("/like/add")
    @exception_handler
    async def add_like(self, comment_id: int, eid: int):
        await self.comment_service.add_like(
            comment_id=comment_id, eid=eid
        )

    @comment_controller.delete("/like/remove")
    @exception_handler
    async def remove_like(self, comment_id: int, eid: int):
        await self.comment_service.remove_like(
            comment_id=comment_id, eid=eid
        )
