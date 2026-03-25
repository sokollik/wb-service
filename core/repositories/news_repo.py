from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    case,
    delete,
    desc,
    exists,
    func,
    or_,
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.emploee import EmployeeOrm
from core.models.enums import NewsStatus
from core.models.news import (
    CategoryOrm,
    CommentOrm,
    NewsAcknowledgementOrm,
    NewsAcknowledgementTargetOrm,
    NewsLikeOrm,
    NewsOrm,
    NewsTagOrm,
    NewsToCategoryOrm,
    NewsToFileOrm,
    TagOrm,
)
from core.models.static import FileOrm


class NewsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_news(
        self,
        category_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: str = "newest",
        limit: int = 15,
        offset: int = 0,
        user_eid: Optional[str] = None,
        likes: Optional[bool] = None,
        status: Optional[NewsStatus] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
    ):
        likes_subq = (
            select(
                NewsLikeOrm.news_id,
                func.count(NewsLikeOrm.user_id).label("likes_count"),
            )
            .group_by(NewsLikeOrm.news_id)
            .subquery()
        )

        comments_subq = (
            select(
                CommentOrm.news_id,
                func.count(CommentOrm.id).label("comments_count"),
            )
            .group_by(CommentOrm.news_id)
            .subquery()
        )

        tags_subq = (
            select(
                NewsTagOrm.news_id, func.json_agg(TagOrm.name).label("tags")
            )
            .join(TagOrm, TagOrm.id == NewsTagOrm.tag_id)
            .group_by(NewsTagOrm.news_id)
            .subquery()
        )
        files_subq = (
            select(
                NewsToFileOrm.news_id,
                func.json_agg(NewsToFileOrm.file_id).label("file_ids"),
            )
            .group_by(NewsToFileOrm.news_id)
            .subquery()
        )

        categories_subq = (
            select(
                NewsToCategoryOrm.news_id,
                func.json_agg(
                    func.json_build_object(
                        "id", CategoryOrm.id, "name", CategoryOrm.name
                    )
                ).label("categories"),
            )
            .join(CategoryOrm, CategoryOrm.id == NewsToCategoryOrm.category_id)
            .group_by(NewsToCategoryOrm.news_id)
            .subquery()
        )

        is_liked_expr = (
            case(
                (
                    exists(
                        select(NewsLikeOrm.user_id).where(
                            (NewsLikeOrm.news_id == NewsOrm.id)
                            & (NewsLikeOrm.user_id == user_eid)
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
                NewsOrm.id,
                NewsOrm.title,
                NewsOrm.short_description,
                NewsOrm.published_at,
                NewsOrm.views_count,
                NewsOrm.is_pinned,
                NewsOrm.comments_enabled,
                EmployeeOrm.full_name.label("author_name"),
                func.coalesce(likes_subq.c.likes_count, 0).label(
                    "likes_count"
                ),
                func.coalesce(comments_subq.c.comments_count, 0).label(
                    "comments_count"
                ),
                func.coalesce(tags_subq.c.tags, func.json_build_array()).label(
                    "tags"
                ),
                func.coalesce(
                    files_subq.c.file_ids, func.json_build_array()
                ).label("file_ids"),
                func.coalesce(
                    categories_subq.c.categories, func.json_build_array()
                ).label("categories"),
                is_liked_expr,
            )
            .join(EmployeeOrm, EmployeeOrm.eid == NewsOrm.author_id)
            .outerjoin(likes_subq, likes_subq.c.news_id == NewsOrm.id)
            .outerjoin(comments_subq, comments_subq.c.news_id == NewsOrm.id)
            .outerjoin(tags_subq, tags_subq.c.news_id == NewsOrm.id)
            .outerjoin(files_subq, files_subq.c.news_id == NewsOrm.id)
            .outerjoin(
                categories_subq, categories_subq.c.news_id == NewsOrm.id
            )
        )

        if likes and user_eid:
            user_likes_subq = (
                select(NewsLikeOrm.news_id)
                .where(NewsLikeOrm.user_id == user_eid)
                .subquery()
            )
            query = query.join(
                user_likes_subq, user_likes_subq.c.news_id == NewsOrm.id
            )

        if category_id:
            query = query.join(
                NewsToCategoryOrm, NewsToCategoryOrm.news_id == NewsOrm.id
            )
            query = query.where(NewsToCategoryOrm.category_id == category_id)

        if date_from:
            query = query.where(NewsOrm.published_at >= date_from)
        if date_to:
            query = query.where(NewsOrm.published_at <= date_to)

        # Фильтрация по статусу (по умолчанию только PUBLISHED)
        if status:
            query = query.where(NewsOrm.status == status)
        else:
            query = query.where(NewsOrm.status == NewsStatus.PUBLISHED)

        # Скрываем истёкшие новости
        query = query.where(
            or_(NewsOrm.expires_at.is_(None), NewsOrm.expires_at > func.now())
        )

        # Фильтрация по тегу
        if tag:
            tag_filter_subq = (
                select(NewsTagOrm.news_id)
                .join(TagOrm, TagOrm.id == NewsTagOrm.tag_id)
                .where(TagOrm.name == tag)
                .subquery()
            )
            query = query.join(
                tag_filter_subq, tag_filter_subq.c.news_id == NewsOrm.id
            )

        # Поиск по заголовку
        if search:
            query = query.where(NewsOrm.title.ilike(f"%{search}%"))

        order_params = [desc(NewsOrm.is_pinned)]
        if sort_by == "popular":
            order_params.append(desc(NewsOrm.views_count))
        elif sort_by == "discussed":
            order_params.append(
                desc(func.coalesce(comments_subq.c.comments_count, 0))
            )
        else:
            order_params.append(desc(NewsOrm.published_at))

        query = query.order_by(*order_params).limit(limit).offset(offset)

        result = await self.session.execute(query)
        return result.mappings().all()

    async def get_news_detail(
        self, news_id: int, user_eid: Optional[str] = None
    ):
        await self.session.execute(
            update(NewsOrm)
            .where(NewsOrm.id == news_id)
            .values(views_count=NewsOrm.views_count + 1)
        )

        files_subq = (
            select(
                func.json_agg(
                    func.json_build_object(
                        "id",
                        FileOrm.id,
                    )
                )
            )
            .join(NewsToFileOrm, NewsToFileOrm.file_id == FileOrm.id)
            .where(NewsToFileOrm.news_id == news_id)
            .scalar_subquery()
        )

        likes_count_subq = (
            select(func.count(NewsLikeOrm.user_id))
            .where(NewsLikeOrm.news_id == news_id)
            .scalar_subquery()
        )

        comments_count_subq = (
            select(func.count(CommentOrm.id))
            .where(CommentOrm.news_id == news_id)
            .scalar_subquery()
        )

        tags_subq = (
            select(
                NewsTagOrm.news_id, func.json_agg(TagOrm.name).label("tags")
            )
            .join(TagOrm, TagOrm.id == NewsTagOrm.tag_id)
            .group_by(NewsTagOrm.news_id)
            .subquery()
        )
        files_subq = (
            select(func.json_agg(NewsToFileOrm.file_id))
            .where(NewsToFileOrm.news_id == news_id)
            .scalar_subquery()
        )
        categories_agg = (
            select(
                func.json_agg(
                    func.json_build_object(
                        "id", CategoryOrm.id, "name", CategoryOrm.name
                    )
                )
            )
            .join(
                NewsToCategoryOrm,
                NewsToCategoryOrm.category_id == CategoryOrm.id,
            )
            .where(NewsToCategoryOrm.news_id == news_id)
            .scalar_subquery()
        )

        is_liked_expr = (
            case(
                (
                    exists(
                        select(NewsLikeOrm.user_id).where(
                            (NewsLikeOrm.news_id == news_id)
                            & (NewsLikeOrm.user_id == user_eid)
                        )
                    ),
                    True,
                ),
                else_=False,
            ).label("is_liked")
            if user_eid
            else func.cast(False, Boolean).label("is_liked")
        )

        is_acknowledged_expr = (
            case(
                (
                    exists(
                        select(NewsAcknowledgementOrm.user_eid).where(
                            (NewsAcknowledgementOrm.news_id == news_id)
                            & (NewsAcknowledgementOrm.user_eid == user_eid)
                        )
                    ),
                    True,
                ),
                else_=False,
            ).label("is_acknowledged")
            if user_eid
            else func.cast(False, Boolean).label("is_acknowledged")
        )

        must_acknowledge_expr = (
            case(
                (
                    NewsOrm.mandatory_ack == True,
                    case(
                        (NewsOrm.ack_target_all == True, True),
                        (
                            exists(
                                select(
                                    NewsAcknowledgementTargetOrm.user_eid
                                ).where(
                                    (
                                        NewsAcknowledgementTargetOrm.news_id
                                        == news_id
                                    )
                                    & (
                                        NewsAcknowledgementTargetOrm.user_eid
                                        == user_eid
                                    )
                                )
                            ),
                            True,
                        ),
                        else_=False,
                    ),
                ),
                else_=False,
            ).label("must_acknowledge")
            if user_eid
            else func.cast(False, Boolean).label("must_acknowledge")
        )

        query = (
            select(
                NewsOrm.id,
                NewsOrm.title,
                NewsOrm.short_description,
                NewsOrm.content,
                NewsOrm.published_at,
                NewsOrm.is_pinned,
                NewsOrm.mandatory_ack,
                NewsOrm.ack_target_all,
                NewsOrm.comments_enabled,
                NewsOrm.scheduled_publish_at,
                NewsOrm.views_count,
                NewsOrm.status,
                EmployeeOrm.full_name.label("author_name"),
                func.coalesce(likes_count_subq, 0).label("likes_count"),
                func.coalesce(comments_count_subq, 0).label("comments_count"),
                func.coalesce(files_subq, func.json_build_array()).label(
                    "file_ids"
                ),
                func.coalesce(tags_subq.c.tags, func.json_build_array()).label(
                    "tags"
                ),
                func.coalesce(categories_agg, func.json_build_array()).label(
                    "categories"
                ),
                is_liked_expr,
                is_acknowledged_expr,
                must_acknowledge_expr,
            )
            .outerjoin(tags_subq, tags_subq.c.news_id == NewsOrm.id)
            .join(EmployeeOrm, EmployeeOrm.eid == NewsOrm.author_id)
            .where(NewsOrm.id == news_id)
        )

        result = await self.session.execute(query)
        return result.mappings().one_or_none()

    async def delete_news(self, news_id: int):
        await self.session.execute(
            delete(NewsOrm).where(NewsOrm.id == news_id)
        )

    async def get_categories(self):
        stmt = select(CategoryOrm).order_by(CategoryOrm.name)
        result = await self.session.execute(stmt)
        res = result.scalars().all()
        return res

    async def create_category(self, name: str):
        category = CategoryOrm(name=name)
        self.session.add(category)
        await self.session.flush()
        return category

    async def publish_scheduled_news(self) -> int:
        """Публикует все новости, у которых наступило время scheduled_publish_at."""
        result = await self.session.execute(
            update(NewsOrm)
            .where(
                NewsOrm.status == NewsStatus.SCHEDULED,
                NewsOrm.scheduled_publish_at <= func.now(),
            )
            .values(
                status=NewsStatus.PUBLISHED,
                published_at=func.now(),
            )
        )
        await self.session.commit()
        return result.rowcount
