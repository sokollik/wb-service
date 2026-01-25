from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from core.common.common_repo import CommonRepository
from core.models.news import CommentOrm, CommentToFileOrm
from core.repositories.comment_repo import CommentRepository
from core.schemas.comment_schema import (
    CommentCreateSchema,
    CommentSchema,
    CommentUpdateSchema,
    CommentViewSchema,
)


class CommentService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.common_repo = CommonRepository(session=self.session)
        self.comment_repo = CommentRepository(session=self.session)

    async def get_comments(
        self, news_id: int, sort_by: Literal["popular", "new"] = "new"
    ) -> CommentViewSchema:
        raw_comments = await self.comment_repo.get_comments(news_id, sort_by)

        if not raw_comments:
            return CommentViewSchema(result=[], count=0)

        all_comments = {
            c["id"]: CommentSchema(**c, replies=[], replies_count=0)
            for c in raw_comments
        }

        root_comments = []

        for comment in all_comments.values():
            if comment.parent_id is None:
                root_comments.append(comment)
            else:
                parent = all_comments.get(comment.parent_id)
                if parent:
                    parent.replies.append(comment)
                    parent.replies_count += 1

        return CommentViewSchema(result=root_comments, count=len(raw_comments))

    async def create_comment(self, comment: CommentCreateSchema):
        new_comment = await self.common_repo.add(
            CommentOrm(
                news_id=comment.news_id,
                author_id=comment.author_id,
                parent_id=comment.parent_id,
                content=comment.content,
            )
        )
        await self.common_repo.add_all(
            [
                CommentToFileOrm(
                    comment_id=new_comment.id,
                    file_id=file_id,
                )
                for file_id in (comment.file_ids or [])
            ]
        )
        return new_comment.id

    async def edit_comment(self, comment: CommentUpdateSchema):
        pass

    async def delete_comment(self, comment_id: int, eid: int):
        pass
