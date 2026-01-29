from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from fastapi_restful.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession

from core.utils.db_util import get_session_obj
from core.utils.common_util import exception_handler
from core.services.news_service import NewsService
from core.schemas.news_schema import (
    CategoryCreateSchema,
    CategorySchema,
    NewsCreateSchema,
    NewsDetailSchema,
    NewsListResponseSchema,
    NewsUpdateSchema,
)

news_router = APIRouter(tags=["News"])


@cbv(news_router)
class NewsController:
    def __init__(self, session: AsyncSession = Depends(get_session_obj)):
        self.session = session
        self.news_service = NewsService(session=session)

    @news_router.get("/", response_model=List[NewsListResponseSchema])
    @exception_handler
    async def get_news(
        self,
        category_id: Optional[int] = Query(None, description="ID рубрики"),
        date_from: Optional[datetime] = Query(None, description="Начало периода"),
        date_to: Optional[datetime] = Query(None, description="Конец периода"),
        sort_by: str = Query("newest", regex="^(newest|popular|discussed)$"),
        page: int = Query(1, ge=1, description="Номер страницы"),
    ):
        """
        Получение списка новостей с фильтрами, сортировкой и пагинацией.
        Закрепленные новости всегда в топе.
        """
        return await self.news_service.get_news_feed(
            category_id=category_id,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            page=page,
        )

    @news_router.get("/categories", response_model=List[CategorySchema])
    @exception_handler
    async def get_categories(self):
        return await self.news_service.list_categories()

    @news_router.post("/categories", response_model=int)
    @exception_handler
    async def create_category(
        self,
        data: CategoryCreateSchema,
    ):
        """Создать новую рубрику (только админ)"""
        return await self.news_service.add_category(data)

    @news_router.get("/{news_id}", response_model=NewsDetailSchema)
    @exception_handler
    async def get_news_by_id(self, news_id: int):
        return await self.news_service.get_news_by_id(news_id)

    @news_router.post("/", status_code=201)
    @exception_handler
    async def create_news(self, data: NewsCreateSchema, user_eid: int):
        return await self.news_service.create_news(author_id=user_eid, data=data)

    @news_router.patch("/{news_id}")
    @exception_handler
    async def update_news(
        self,
        news_id: int,
        data: NewsUpdateSchema,
        user_eid: int,
    ):
        return await self.news_service.update_news(news_id, user_eid, data)

    @news_router.delete("/{news_id}")
    @exception_handler
    async def delete_news(
        self,
        news_id: int,
        user_eid: int,
    ):
        return await self.news_service.delete_news(news_id, user_eid)

    @news_router.delete("/categories/{category_id}")
    @exception_handler
    async def delete_category(
        self,
        category_id: int,
    ):
        await self.news_service.remove_category(category_id)
