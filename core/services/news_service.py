from datetime import datetime
from typing import Optional
import json

from sqlalchemy.ext.asyncio import AsyncSession
from pydantic.json import pydantic_encoder

from core.common.common_exc import NotFoundHttpException
from core.common.common_repo import CommonRepository
from core.models.news import (
    CategoryOrm,
    NewsLikeOrm,
    NewsOrm,
    NewsTagOrm,
    TagOrm,
    NewsToCategoryOrm,
    NewsToFileOrm,
    NewsChangeLogOrm,
)
from core.models.enums import ProfileOperationType
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
        user_eid: Optional[str] = None,
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

    async def get_news_by_id(self, news_id: int, user_eid: Optional[str] = None):
        news = await self.news_repo.get_news_detail(news_id, user_eid=user_eid)
        if not news:
            raise NotFoundHttpException(name="news")
        return news

    async def create_news(self, author_id: str, data: NewsCreateSchema):
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

        # Логируем создание новости
        await self._log_news_change(
            news_id=new_news.id,
            changed_by_eid=author_id,
            field_name="news_created",
            old_value=None,
            new_value={
                "title": data.title,
                "short_description": data.short_description,
                "content": data.content,
                "is_pinned": data.is_pinned,
                "mandatory_ack": data.mandatory_ack,
            },
            operation=ProfileOperationType.CREATE,
        )

        if data.category_ids:
            cat_links = [
                NewsToCategoryOrm(news_id=new_news.id, category_id=c_id)
                for c_id in data.category_ids
            ]
            await self.common_repo.add_all(cat_links)
            await self._log_news_change(
                news_id=new_news.id,
                changed_by_eid=author_id,
                field_name="categories",
                old_value=None,
                new_value=data.category_ids,
                operation=ProfileOperationType.CREATE,
            )

        if data.file_ids:
            file_links = [
                NewsToFileOrm(news_id=new_news.id, file_id=f_id)
                for f_id in data.file_ids
            ]
            await self.common_repo.add_all(file_links)
            await self._log_news_change(
                news_id=new_news.id,
                changed_by_eid=author_id,
                field_name="files",
                old_value=None,
                new_value=data.file_ids,
                operation=ProfileOperationType.CREATE,
            )

        for t_name in data.tag_names:
            tag = await self.common_repo.add(
                TagOrm(name=t_name), where_stmt=(TagOrm.name == t_name,)
            )

            await self.common_repo.add(NewsTagOrm(news_id=new_news.id, tag_id=tag.id))

        if data.tag_names:
            await self._log_news_change(
                news_id=new_news.id,
                changed_by_eid=author_id,
                field_name="tags",
                old_value=None,
                new_value=data.tag_names,
                operation=ProfileOperationType.CREATE,
            )

        await self.common_repo.session.commit()
        return new_news.id

    async def update_news(self, news_id: int, user_eid: str, data: NewsUpdateSchema):

        news = await self.common_repo.get_one(NewsOrm, (NewsOrm.id == news_id))
        if not news:
            raise NotFoundHttpException(name="news")

        update_data = data.model_dump(exclude_unset=True)

        tag_names = update_data.pop("tag_names", None)
        file_ids = update_data.pop("file_ids", None)
        category_ids = update_data.pop("category_ids", None)

        # Логируем изменения полей основной таблицы
        if update_data:
            for field_name, new_value in update_data.items():
                old_value = getattr(news, field_name, None)
                await self._log_news_change(
                    news_id=news_id,
                    changed_by_eid=user_eid,
                    field_name=field_name,
                    old_value=old_value,
                    new_value=new_value,
                    operation=ProfileOperationType.UPDATE,
                )
            await self.common_repo.update_stmt(
                table=NewsOrm,
                where_stmt=(NewsOrm.id == news_id),
                values=update_data,
            )

        # Логируем изменение категорий
        if category_ids is not None:
            old_categories = await self.common_repo.get_all_scalars(
                NewsToCategoryOrm, where_stmt=(NewsToCategoryOrm.news_id == news_id)
            )
            old_category_ids = [cat.category_id for cat in old_categories]

            await self.common_repo.delete(
                NewsToCategoryOrm, (NewsToCategoryOrm.news_id == news_id)
            )
            if category_ids:
                new_cats = [
                    NewsToCategoryOrm(news_id=news_id, category_id=c_id)
                    for c_id in category_ids
                ]
                await self.common_repo.add_all(new_cats)

            await self._log_news_change(
                news_id=news_id,
                changed_by_eid=user_eid,
                field_name="categories",
                old_value=old_category_ids,
                new_value=category_ids,
                operation=ProfileOperationType.UPDATE,
            )

        # Логируем изменение тегов
        if tag_names is not None:
            old_tags = await self.common_repo.get_all_scalars(
                NewsTagOrm, where_stmt=(NewsTagOrm.news_id == news_id)
            )
            old_tag_ids = [tag.tag_id for tag in old_tags]

            await self.common_repo.delete(NewsTagOrm, (NewsTagOrm.news_id == news_id))
            for t_name in tag_names:
                tag = await self.common_repo.add(
                    TagOrm(name=t_name), where_stmt=(TagOrm.name == t_name,)
                )
                await self.common_repo.add(NewsTagOrm(news_id=news_id, tag_id=tag.id))

            await self._log_news_change(
                news_id=news_id,
                changed_by_eid=user_eid,
                field_name="tags",
                old_value=tag_names if not old_tag_ids else None,
                new_value=tag_names,
                operation=ProfileOperationType.UPDATE,
            )

        # Логируем изменение файлов
        if file_ids is not None:
            old_files = await self.common_repo.get_all_scalars(
                NewsToFileOrm, where_stmt=(NewsToFileOrm.news_id == news_id)
            )
            old_file_ids = [f.file_id for f in old_files]

            await self.common_repo.delete(
                NewsToFileOrm, (NewsToFileOrm.news_id == news_id)
            )
            file_links = [
                NewsToFileOrm(news_id=news_id, file_id=f_id) for f_id in file_ids
            ]
            if file_links:
                await self.common_repo.add_all(file_links)

            await self._log_news_change(
                news_id=news_id,
                changed_by_eid=user_eid,
                field_name="files",
                old_value=old_file_ids,
                new_value=file_ids,
                operation=ProfileOperationType.UPDATE,
            )

    async def delete_news(self, news_id: int, user_eid: str):
        # Получаем информацию о новости перед удалением
        news = await self.common_repo.get_one(NewsOrm, (NewsOrm.id == news_id))
        if not news:
            raise NotFoundHttpException(name="news")

        # Логируем удаление
        await self._log_news_change(
            news_id=news_id,
            changed_by_eid=user_eid,
            field_name="news_deleted",
            old_value={
                "title": news.title,
                "short_description": news.short_description,
                "content": news.content,
                "author_id": news.author_id,
                "is_pinned": news.is_pinned,
                "mandatory_ack": news.mandatory_ack,
                "status": news.status,
            },
            new_value=None,
            operation=ProfileOperationType.DELETE,
        )

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

    async def add_like(self, news_id: int, eid: str):
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

    async def remove_like(self, news_id: int, eid: str):
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

    async def _log_news_change(
        self,
        news_id: int,
        changed_by_eid: str,
        field_name: str,
        old_value: any,
        new_value: any,
        operation: ProfileOperationType,
    ):
        """Логирует изменение новости в таблицу news_change_log"""
        log_entry = NewsChangeLogOrm(
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

    async def get_news_edit_log(self, news_id: int):
        """Получает историю всех изменений новости"""
        logs = await self.common_repo.get_all_scalars(
            NewsChangeLogOrm,
            where_stmt=NewsChangeLogOrm.news_id == news_id,
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
