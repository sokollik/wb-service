from typing import Literal, Optional

from sqlalchemy import Boolean, case, desc, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.emploee import EmployeeOrm
from core.models.news import CommentLikeOrm, CommentOrm, CommentToFileOrm


class CommentRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_comments(
        self,
        news_id: int,
        sort_by: Literal["popular", "new"] = "new",
        user_eid: Optional[str] = None,
    ):
        files_subq = (
            select(
                CommentToFileOrm.comment_id,
                func.json_agg(CommentToFileOrm.file_id).label("file_ids"),
            )
            .group_by(CommentToFileOrm.comment_id)
            .subquery()
        )

        likes_subq = (
            select(
                CommentLikeOrm.comment_id,
                func.count(CommentLikeOrm.user_id).label("likes_count"),
            )
            .group_by(CommentLikeOrm.comment_id)
            .subquery()
        )

        is_liked_expr = (
            case(
                (
                    exists(
                        select(CommentLikeOrm.user_id).where(
                            (CommentLikeOrm.comment_id == CommentOrm.id)
                            & (CommentLikeOrm.user_id == user_eid)
                        )
                    ),
                    True,
                ),
                else_=False,
            ).label("is_liked")
            if user_eid
            else func.cast(False, Boolean).label("is_liked")
        )

        query = (
            select(
                CommentOrm.id,
                CommentOrm.parent_id,
                CommentOrm.content,
                CommentOrm.created_at,
                CommentOrm.is_edited,
                CommentOrm.news_id,
                func.json_build_object(
                    "eid", EmployeeOrm.eid, "full_name", EmployeeOrm.full_name
                ).label("author"),
                func.coalesce(likes_subq.c.likes_count, 0).label(
                    "likes_count"
                ),
                func.coalesce(
                    files_subq.c.file_ids, func.json_build_array()
                ).label("file_ids"),
                is_liked_expr,
            )
            .join(EmployeeOrm, CommentOrm.author_id == EmployeeOrm.eid)
            .outerjoin(likes_subq, CommentOrm.id == likes_subq.c.comment_id)
            .outerjoin(files_subq, CommentOrm.id == files_subq.c.comment_id)
            .where(CommentOrm.news_id == news_id)
        )

        if sort_by == "popular":
            query = query.order_by(
                desc("likes_count"), desc(CommentOrm.created_at)
            )
        else:
            query = query.order_by(desc(CommentOrm.created_at))

        result = await self.session.execute(query)
        return result.mappings().all()
