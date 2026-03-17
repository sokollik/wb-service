import json
import re
from typing import Literal

from pydantic.json import pydantic_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.common.common_exc import (
    NotAllowedHttpException,
    NotFoundHttpException,
)
from core.common.common_repo import CommonRepository
from core.models.emploee import EmployeeOrm
from core.models.enums import ProfileOperationType
from core.models.news import (
    CommentChangeLogOrm,
    CommentOrm,
    CommentToFileOrm,
    MentionOrm,
    NewsOrm,
)
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
        self,
        news_id: int,
        sort_by: Literal["popular", "new"] = "new",
        user_eid: str | None = None,
    ) -> CommentViewSchema:
        raw_comments = await self.comment_repo.get_comments(
            news_id, sort_by, user_eid=user_eid
        )

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

    async def create_comment(self, comment: CommentCreateSchema, author_eid: str):
        news = await self.common_repo.get_one(
            from_table=NewsOrm, where_stmt=(NewsOrm.id == comment.news_id)
        )
        if not news:
            raise NotFoundHttpException(name="news")
        if not news.comments_enabled:
            raise NotAllowedHttpException(name="comments")

        new_comment = await self.common_repo.add(
            CommentOrm(
                news_id=comment.news_id,
                author_id=author_eid,
                parent_id=comment.parent_id,
                content=comment.content,
            )
        )

        await self._log_comment_change(
            comment_id=new_comment.id,
            news_id=comment.news_id,
            changed_by_eid=author_eid,
            field_name="comment_created",
            old_value=None,
            new_value={
                "content": comment.content,
                "parent_id": comment.parent_id,
            },
            operation=ProfileOperationType.CREATE,
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

        if comment.file_ids:
            await self._log_comment_change(
                comment_id=new_comment.id,
                news_id=comment.news_id,
                changed_by_eid=author_eid,
                field_name="files",
                old_value=None,
                new_value=comment.file_ids,
                operation=ProfileOperationType.CREATE,
            )

        await self._process_mentions(new_comment.id, comment.content)

        return new_comment.id

    async def edit_comment(self, comment: CommentUpdateSchema, editor_eid: str):
        existing_comment = await self.common_repo.get_one(
            from_table=CommentOrm, where_stmt=(CommentOrm.id == comment.id)
        )
        if not existing_comment:
            raise NotFoundHttpException(name="comment")
        if existing_comment.author_id != editor_eid:
            raise NotAllowedHttpException(name="edit")

        old_content = existing_comment.content
        existing_comment.content = comment.content
        existing_comment.is_edited = True

        await self._log_comment_change(
            comment_id=comment.id,
            news_id=existing_comment.news_id,
            changed_by_eid=editor_eid,
            field_name="content",
            old_value=old_content,
            new_value=comment.content,
            operation=ProfileOperationType.UPDATE,
        )

        old_files = await self.common_repo.get_all_scalars(
            CommentToFileOrm, where_stmt=(CommentToFileOrm.comment_id == comment.id)
        )
        old_file_ids = [f.file_id for f in old_files]

        await self.common_repo.delete(
            from_table=CommentToFileOrm,
            where_stmt=(CommentToFileOrm.comment_id == comment.id),
        )
        await self.common_repo.add_all(
            [
                CommentToFileOrm(
                    comment_id=comment.id,
                    file_id=file_id,
                )
                for file_id in (comment.file_ids or [])
            ]
        )

        if comment.file_ids != old_file_ids:
            await self._log_comment_change(
                comment_id=comment.id,
                news_id=existing_comment.news_id,
                changed_by_eid=editor_eid,
                field_name="files",
                old_value=old_file_ids,
                new_value=comment.file_ids,
                operation=ProfileOperationType.UPDATE,
            )

        await self.common_repo.delete(
            from_table=MentionOrm,
            where_stmt=(MentionOrm.comment_id == comment.id),
        )
        await self._process_mentions(comment.id, comment.content)

    async def delete_comment(self, comment_id: int, eid: str, roles: list[str] = None):
        existing_comment = await self.common_repo.get_one(
            from_table=CommentOrm, where_stmt=(CommentOrm.id == comment_id)
        )
        if not existing_comment:
            raise NotFoundHttpException(name="comment")
        is_moderator = roles and ("admin" in roles or "news_editor" in roles)
        if existing_comment.author_id != eid and not is_moderator:
            raise NotAllowedHttpException(name="delete")

        await self._log_comment_change(
            comment_id=comment_id,
            news_id=existing_comment.news_id,
            changed_by_eid=eid,
            field_name="comment_deleted",
            old_value={
                "content": existing_comment.content,
                "author_id": existing_comment.author_id,
                "parent_id": existing_comment.parent_id,
            },
            new_value=None,
            operation=ProfileOperationType.DELETE,
        )

        await self.common_repo.delete(
            from_table=CommentOrm,
            where_stmt=(CommentOrm.id == comment_id),
        )

    async def add_like(self, comment_id: int, eid: str):
        existing_comment = await self.common_repo.get_one(
            from_table=CommentOrm, where_stmt=(CommentOrm.id == comment_id)
        )
        if not existing_comment:
            raise NotFoundHttpException(name="comment")

        from core.models.news import CommentLikeOrm

        existing_like = await self.common_repo.get_one(
            from_table=CommentLikeOrm,
            where_stmt=(
                (CommentLikeOrm.comment_id == comment_id),
                (CommentLikeOrm.user_id == eid),
            ),
        )
        if existing_like:
            return

        await self.common_repo.add(CommentLikeOrm(comment_id=comment_id, user_id=eid))

    async def remove_like(self, comment_id: int, eid: str):
        existing_comment = await self.common_repo.get_one(
            from_table=CommentOrm, where_stmt=(CommentOrm.id == comment_id)
        )
        if not existing_comment:
            raise NotFoundHttpException(name="comment")

        from core.models.news import CommentLikeOrm

        existing_like = await self.common_repo.get_one(
            from_table=CommentLikeOrm,
            where_stmt=(
                (CommentLikeOrm.comment_id == comment_id),
                (CommentLikeOrm.user_id == eid),
            ),
        )
        if not existing_like:
            return

        await self.common_repo.delete(
            from_table=CommentLikeOrm,
            where_stmt=(
                (CommentLikeOrm.comment_id == comment_id),
                (CommentLikeOrm.user_id == eid),
            ),
        )

    async def _process_mentions(self, comment_id: int, content: str):

        mention_pattern = re.compile(r"@([\w.]+(?:\s[\w.]+)?)", re.UNICODE)
        raw_mentions = mention_pattern.findall(content)

        if not raw_mentions:
            return

        for mention_name in set(raw_mentions):
            result = await self.session.execute(
                select(EmployeeOrm.eid).where(
                    EmployeeOrm.full_name.ilike(f"%{mention_name}%")
                )
            )
            employees = result.scalars().all()
            for eid in employees:
                await self.common_repo.add(
                    MentionOrm(comment_id=comment_id, mentioned_user_id=eid)
                )

    async def _log_comment_change(
        self,
        comment_id: int,
        news_id: int,
        changed_by_eid: str,
        field_name: str,
        old_value: any,
        new_value: any,
        operation: ProfileOperationType,
    ):
        log_entry = CommentChangeLogOrm(
            comment_id=comment_id,
            news_id=news_id,
            changed_by_eid=changed_by_eid,
            field_name=field_name,
            old_value=(
                json.dumps(old_value, default=pydantic_encoder)
                if old_value is not None
                else None
            ),
            new_value=(
                json.dumps(new_value, default=pydantic_encoder)
                if new_value is not None
                else None
            ),
            operation=operation,
        )
        await self.common_repo.add(log_entry)

    async def get_comment_edit_log(self, comment_id: int):
        logs = await self.common_repo.get_all_scalars(
            CommentChangeLogOrm,
            where_stmt=CommentChangeLogOrm.comment_id == comment_id,
        )
        processed_logs = []
        for log in logs:

            def try_json(val):
                if val is None:
                    return None
                try:
                    return json.loads(val)
                except (TypeError, json.JSONDecodeError):
                    return val

            log_data = {
                "id": log.id,
                "comment_id": log.comment_id,
                "news_id": log.news_id,
                "changed_by_eid": log.changed_by_eid,
                "changed_at": log.changed_at,
                "field_name": log.field_name,
                "operation": log.operation,
                "old_value": try_json(log.old_value),
                "new_value": try_json(log.new_value),
            }
            processed_logs.append(log_data)
        return processed_logs
