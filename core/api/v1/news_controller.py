from datetime import datetime
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Query
from fastapi_restful.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession

from core.api.deps import CurrentUser, require_roles
from core.models.enums import NewsStatus
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
        current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
        category_id: Optional[int] = Query(None),
        date_from: Optional[datetime] = Query(None),
        date_to: Optional[datetime] = Query(None),
        sort_by: Literal["newest", "popular", "discussed"] = Query("newest"),
        page: int = Query(1),
        size: int = Query(15),
        likes: Optional[bool] = Query(None),
        status: Optional[NewsStatus] = Query(None),
        tag: Optional[str] = Query(None),
        search: Optional[str] = Query(None),
    ):
        return await self.news_service.get_news(
            category_id=category_id,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            page=page,
            size=size,
            user_eid=current_user.eid,
            likes=likes,
            status=status,
            tag=tag,
            search=search,
        )

    @news_router.get("/categories", response_model=List[CategorySchema])
    @exception_handler
    async def get_categories(
        self,
        _current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
    ):
        return await self.news_service.get_categories()

    @news_router.post("/categories", response_model=int)
    @exception_handler
    async def create_category(
        self,
        data: CategoryCreateSchema,
        _current_user: CurrentUser = Depends(require_roles(["admin"])),
    ):
        return await self.news_service.add_category(data)

    @news_router.get("/categories/followed", response_model=List[CategorySchema])
    @exception_handler
    async def get_followed_categories(
        self,
        current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
    ):
        return await self.news_service.get_followed_categories(
            user_eid=current_user.eid
        )

    @news_router.post("/categories/{category_id}/follow")
    @exception_handler
    async def follow_category(
        self,
        category_id: int,
        current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
    ):
        await self.news_service.follow_category(
            category_id=category_id, user_eid=current_user.eid
        )

    @news_router.delete("/categories/{category_id}/follow")
    @exception_handler
    async def unfollow_category(
        self,
        category_id: int,
        current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
    ):
        await self.news_service.unfollow_category(
            category_id=category_id, user_eid=current_user.eid
        )

    @news_router.get("/{news_id}", response_model=NewsFullSchema)
    @exception_handler
    async def get_news_by_id(
        self,
        news_id: int,
        current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
    ):
        return await self.news_service.get_news_by_id(
            news_id, user_eid=current_user.eid
        )

    @news_router.post("/", response_model=int)
    @exception_handler
    async def create_news(
        self,
        data: NewsCreateSchema,
        current_user: CurrentUser = Depends(
            require_roles(["news_editor", "admin"])
        ),
    ):
        return await self.news_service.create_news(
            author_id=current_user.eid, data=data
        )

    @news_router.patch("/{news_id}")
    @exception_handler
    async def update_news(
        self,
        news_id: int,
        data: NewsUpdateSchema,
        current_user: CurrentUser = Depends(
            require_roles(["news_editor", "admin"])
        ),
    ):
        return await self.news_service.update_news(
            news_id=news_id, user_eid=current_user.eid, data=data
        )

    @news_router.delete("/{news_id}")
    @exception_handler
    async def delete_news(
        self,
        news_id: int,
        current_user: CurrentUser = Depends(
            require_roles(["news_editor", "admin"])
        ),
    ):
        return await self.news_service.delete_news(news_id, current_user.eid)

    @news_router.post("/like/add")
    @exception_handler
    async def add_like(
        self,
        news_id: int,
        current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
    ):
        await self.news_service.add_like(news_id=news_id, eid=current_user.eid)

    @news_router.delete("/like/remove")
    @exception_handler
    async def remove_like(
        self,
        news_id: int,
        current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
    ):
        await self.news_service.remove_like(
            news_id=news_id, eid=current_user.eid
        )

    @news_router.delete("/categories/{category_id}")
    @exception_handler
    async def delete_category(
        self,
        category_id: int,
        current_user: CurrentUser = Depends(require_roles(["admin"])),
    ):
        await self.news_service.delete_category(category_id)

    @news_router.get("/{news_id}/log")
    @exception_handler
    async def get_news_edit_log(
        self,
        news_id: int,
        current_user: CurrentUser = Depends(require_roles(["admin"])),
    ):
        return await self.news_service.get_news_edit_log(news_id=news_id)

    @news_router.post("/{news_id}/acknowledge")
    @exception_handler
    async def acknowledge_news(
        self,
        news_id: int,
        current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin", "news_editor"])
        ),
    ):
        await self.news_service.acknowledge_news(
            news_id=news_id, user_eid=current_user.eid
        )

    @news_router.get("/{news_id}/acknowledgements")
    @exception_handler
    async def get_acknowledgements(
        self,
        news_id: int,
        current_user: CurrentUser = Depends(require_roles(["admin"])),
    ):
        return await self.news_service.get_acknowledgements(news_id=news_id)
