from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.common.common_exc import NotFoundHttpException
from core.common.common_repo import CommonRepository
from core.models.news import (
    CategoryOrm,
    NewsLikeOrm,
    NewsOrm,
    NewsTagOrm,
    NewsToCategoryOrm,
    NewsToFileOrm,
    TagOrm,
)
from core.repositories.news_repo import NewsRepository
from core.schemas.news_schema import (
    CategoryCreateSchema,
    NewsCreateSchema,
    NewsUpdateSchema,
)


class NewsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.news_repo = NewsRepository(session=self.session)
        self.common_repo = CommonRepository(session=self.session)

    async def get_news(
        self,
        category_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: str = "newest",
        page: int = 1,
        size: int = 15,
        user_eid: Optional[int] = None,
        likes: Optional[bool] = None,
    ):
        offset = (page - 1) * size

        news_items = await self.news_repo.get_news(
            category_id=category_id,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            limit=size,
            offset=offset,
            user_eid=user_eid,
            likes=likes,
        )

        return news_items

    async def get_news_by_id(
        self, news_id: int, user_eid: Optional[int] = None
    ):
        news = await self.news_repo.get_news_detail(news_id, user_eid=user_eid)
        if not news:
            raise NotFoundHttpException(name="news")
        return news

    async def create_news(self, author_id: int, data: NewsCreateSchema):
        new_news = await self.common_repo.add(
            NewsOrm(
                title=data.title,
                short_description=data.short_description,
                content=data.content,
                author_id=author_id,
                is_pinned=data.is_pinned,
                mandatory_ack=data.mandatory_ack,
            )
        )

        if data.category_ids:
            cat_links = [
                NewsToCategoryOrm(news_id=new_news.id, category_id=c_id)
                for c_id in data.category_ids
            ]
            await self.common_repo.add_all(cat_links)

        if data.file_ids:
            file_links = [
                NewsToFileOrm(news_id=new_news.id, file_id=f_id)
                for f_id in data.file_ids
            ]
            await self.common_repo.add_all(file_links)

        for t_name in data.tag_names:
            tag = await self.common_repo.add(
                TagOrm(name=t_name), where_stmt=(TagOrm.name == t_name,)
            )

            await self.common_repo.add(
                NewsTagOrm(news_id=new_news.id, tag_id=tag.id)
            )

        await self.common_repo.session.commit()
        return new_news.id

    async def update_news(
        self, news_id: int, user_eid: int, data: NewsUpdateSchema
    ):

        news = await self.common_repo.get_one(NewsOrm, (NewsOrm.id == news_id))
        if not news:
            raise NotFoundHttpException(name="news")

        update_data = data.model_dump(exclude_unset=True)

        tag_names = update_data.pop("tag_names", None)
        file_ids = update_data.pop("file_ids", None)
        category_ids = update_data.pop("category_ids", None)

        if update_data:
            await self.common_repo.update_stmt(
                table=NewsOrm,
                where_stmt=(NewsOrm.id == news_id),
                values=update_data,
            )

        if category_ids is not None:
            await self.common_repo.delete(
                NewsToCategoryOrm, (NewsToCategoryOrm.news_id == news_id)
            )
            if category_ids:
                new_cats = [
                    NewsToCategoryOrm(news_id=news_id, category_id=c_id)
                    for c_id in category_ids
                ]
                await self.common_repo.add_all(new_cats)

        if tag_names is not None:
            await self.common_repo.delete(
                NewsTagOrm, (NewsTagOrm.news_id == news_id)
            )
            for t_name in tag_names:
                tag = await self.common_repo.add(
                    TagOrm(name=t_name), where_stmt=(TagOrm.name == t_name,)
                )
                await self.common_repo.add(
                    NewsTagOrm(news_id=news_id, tag_id=tag.id)
                )

        if file_ids is not None:
            await self.common_repo.delete(
                NewsToFileOrm, (NewsToFileOrm.news_id == news_id)
            )
            file_links = [
                NewsToFileOrm(news_id=news_id, file_id=f_id)
                for f_id in file_ids
            ]
            if file_links:
                await self.common_repo.add_all(file_links)

    async def delete_news(self, news_id: int, user_eid: int):
        await self.common_repo.delete(
            from_table=NewsOrm, where_stmt=(NewsOrm.id == news_id)
        )

    async def get_categories(self):
        return await self.news_repo.get_categories()

    async def add_category(self, data: CategoryCreateSchema):
        new_category = await self.common_repo.add(
            orm_instance=CategoryOrm(name=data.name)
        )
        return new_category.id

    async def delete_category(self, category_id: int):
        await self.common_repo.delete(
            from_table=CategoryOrm, where_stmt=(CategoryOrm.id == category_id)
        )

    async def add_like(self, news_id: int, eid: int):
        existing_news = await self.common_repo.get_one(
            from_table=NewsOrm, where_stmt=(NewsOrm.id == news_id)
        )
        if not existing_news:
            raise NotFoundHttpException(name="news")

        existing_like = await self.common_repo.get_one(
            from_table=NewsLikeOrm,
            where_stmt=(
                (NewsLikeOrm.news_id == news_id),
                (NewsLikeOrm.user_id == eid),
            ),
        )
        if existing_like:
            return

        await self.common_repo.add(NewsLikeOrm(news_id=news_id, user_id=eid))

    async def remove_like(self, news_id: int, eid: int):
        existing_news = await self.common_repo.get_one(
            from_table=NewsOrm, where_stmt=(NewsOrm.id == news_id)
        )
        if not existing_news:
            raise NotFoundHttpException(name="news")

        existing_like = await self.common_repo.get_one(
            from_table=NewsLikeOrm,
            where_stmt=(
                (NewsLikeOrm.news_id == news_id),
                (NewsLikeOrm.user_id == eid),
            ),
        )
        if not existing_like:
            return

        await self.common_repo.delete(
            from_table=NewsLikeOrm,
            where_stmt=(
                (NewsLikeOrm.news_id == news_id),
                (NewsLikeOrm.user_id == eid),
            ),
        )
