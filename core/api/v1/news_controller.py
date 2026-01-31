from datetime import datetime
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Query
from fastapi_restful.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession

from core.schemas.news_schema import (
    CategoryCreateSchema,
    CategorySchema,
    NewsCreateSchema,
    NewsFullSchema,
    NewsListResponseSchema,
    NewsUpdateSchema,
)
from core.services.news_service import NewsService
from core.utils.common_util import exception_handler
from core.utils.db_util import get_session_obj

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
        category_id: Optional[int] = Query(None),
        date_from: Optional[datetime] = Query(None),
        date_to: Optional[datetime] = Query(None),
        sort_by: Literal["newest", "popular", "discussed"] = Query("newest"),
        page: int = Query(1),
        size: int = Query(15),
        user_eid: Optional[int] = Query(None),
        likes: Optional[bool] = Query(None),
    ):
        return await self.news_service.get_news(
            category_id=category_id,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            page=page,
            size=size,
            user_eid=user_eid,
            likes=likes,
        )

    @news_router.get("/categories", response_model=List[CategorySchema])
    @exception_handler
    async def get_categories(self):
        return await self.news_service.get_categories()

    @news_router.post("/categories", response_model=int)
    @exception_handler
    async def create_category(
        self,
        data: CategoryCreateSchema,
    ):
        return await self.news_service.add_category(data)

    @news_router.get("/{news_id}", response_model=NewsFullSchema)
    @exception_handler
    async def get_news_by_id(
        self, news_id: int, user_eid: Optional[int] = Query(None)
    ):
        return await self.news_service.get_news_by_id(
            news_id, user_eid=user_eid
        )

    @news_router.post("/", response_model=int)
    @exception_handler
    async def create_news(self, data: NewsCreateSchema, user_eid: int):
        return await self.news_service.create_news(
            author_id=user_eid, data=data
        )

    @news_router.patch("/{news_id}")
    @exception_handler
    async def update_news(
        self,
        news_id: int,
        data: NewsUpdateSchema,
        user_eid: int,
    ):
        return await self.news_service.update_news(
            news_id=news_id, user_eid=user_eid, data=data
        )

    @news_router.delete("/{news_id}")
    @exception_handler
    async def delete_news(
        self,
        news_id: int,
        user_eid: int,
    ):
        return await self.news_service.delete_news(news_id, user_eid)

    @news_router.post("/like/add")
    @exception_handler
    async def add_like(self, news_id: int, eid: int):
        await self.news_service.add_like(news_id=news_id, eid=eid)

    @news_router.delete("/like/remove")
    @exception_handler
    async def remove_like(self, news_id: int, eid: int):
        await self.news_service.remove_like(news_id=news_id, eid=eid)

    @news_router.delete("/categories/{category_id}")
    @exception_handler
    async def delete_category(
        self,
        category_id: int,
    ):
        await self.news_service.delete_category(category_id)
