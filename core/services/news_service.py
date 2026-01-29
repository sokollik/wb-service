from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from core.common.common_exc import NotFoundHttpException
from core.common.common_repo import CommonRepository
from core.models.news import CategoryOrm, NewsOrm
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

    async def get_news_feed(
        self,
        category_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: str = "newest",
        page: int = 1,
    ):
        page_size = 15
        offset = (page - 1) * page_size

        news_items = await self.news_repo.get_news_list(
            category_id=category_id,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            limit=page_size,
            offset=offset,
        )

        return news_items

    async def get_news_by_id(self, news_id: int):
        news = await self.news_repo.get_news_detail(news_id)
        if not news:
            raise NotFoundHttpException(name=f"News with id {news_id}")
        return news

    async def create_news(self, author_id: int, data: NewsCreateSchema):
        news_id = await self.news_repo.create_news(author_id, data)
        return news_id

    async def update_news(self, news_id: int, user_id: int, data: NewsUpdateSchema):
        # 1. Проверяем существование новости
        news = await self.common_repo.get_one(NewsOrm, (NewsOrm.id == news_id))
        if not news:
            raise NotFoundHttpException(name=f"News with id {news_id}")

        update_data = data.model_dump(exclude_unset=True)
        
        # Извлекаем списки связей, чтобы обработать их отдельно
        tag_names = update_data.pop("tag_names", None)
        file_ids = update_data.pop("file_ids", None)
        category_id = update_data.pop("category_id", None)

        # 4. Обновляем основные поля новости
        if update_data:
            await self.news_repo.update_news_fields(news_id, update_data)

        # 5. Синхронизируем связи (если они переданы в запросе)
        if category_id is not None:
            await self.news_repo.update_news_category(news_id, category_id)
        
        if tag_names is not None:
            await self.news_repo.update_news_tags(news_id, tag_names)
            
        if file_ids is not None:
            await self.news_repo.update_news_files(news_id, file_ids)

    async def list_categories(self):
        return await self.news_repo.get_all_categories()

    async def add_category(self, data: CategoryCreateSchema):
        new_category = await self.common_repo.add(
            orm_instance=CategoryOrm(name=data.name)
        )
        return new_category.id

    async def remove_category(self, category_id: int):

        await self.news_repo.delete_category(category_id)
        await self.session.commit()
