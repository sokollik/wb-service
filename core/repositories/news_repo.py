from datetime import datetime
from typing import Optional
from sqlalchemy import delete, insert, select, update, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from core.models.news import NewsOrm, NewsLikeOrm, CommentOrm, NewsTagOrm, NewsToCategoryOrm, CategoryOrm, NewsToFileOrm, TagOrm
from core.models.emploee import EmployeeOrm
from core.models.static import FileOrm
from core.schemas.news_schema import NewsCreateSchema


class NewsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_news_list(
        self,
        category_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: str = "newest",
        limit: int = 15,
        offset: int = 0
    ):
        # Подзапрос для лайков
        likes_subq = (
            select(NewsLikeOrm.news_id, func.count(NewsLikeOrm.user_id).label("likes_count"))
            .group_by(NewsLikeOrm.news_id)
            .subquery()
        )

        # Подзапрос для комментариев
        comments_subq = (
            select(CommentOrm.news_id, func.count(CommentOrm.id).label("comments_count"))
            .group_by(CommentOrm.news_id)
            .subquery()
        )

        # Основной запрос
        query = (
            select(
                NewsOrm.id,
                NewsOrm.title,
                NewsOrm.short_description,
                NewsOrm.published_at,
                NewsOrm.views_count,
                NewsOrm.is_pinned,
                EmployeeOrm.full_name.label("author_name"),
                func.coalesce(likes_subq.c.likes_count, 0).label("likes_count"),
                func.coalesce(comments_subq.c.comments_count, 0).label("comments_count")
            )
            .join(EmployeeOrm, EmployeeOrm.eid == NewsOrm.author_id)
            .outerjoin(likes_subq, likes_subq.c.news_id == NewsOrm.id)
            .outerjoin(comments_subq, comments_subq.c.news_id == NewsOrm.id)
        )

        # Фильтрация по категории
        if category_id:
            query = query.join(NewsToCategoryOrm, NewsToCategoryOrm.news_id == NewsOrm.id)
            query = query.where(NewsToCategoryOrm.category_id == category_id)

        # Фильтрация по дате
        if date_from:
            query = query.where(NewsOrm.published_at >= date_from)
        if date_to:
            query = query.where(NewsOrm.published_at <= date_to)

        # Логика сортировки (is_pinned ВСЕГДА первый)
        order_params = [desc(NewsOrm.is_pinned)]
        
        if sort_by == "popular":
            order_params.append(desc(NewsOrm.views_count))
        elif sort_by == "discussed":
            order_params.append(desc(func.coalesce(comments_subq.c.comments_count, 0)))
        else:  # newest
            order_params.append(desc(NewsOrm.published_at))

        query = query.order_by(*order_params).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return result.mappings().all()


    async def get_news_detail(self, news_id: int):
        # 1. Атомарное увеличение счетчика просмотров
        await self.session.execute(
            update(NewsOrm)
            .where(NewsOrm.id == news_id)
            .values(views_count=NewsOrm.views_count + 1)
        )

        # 2. Подзапрос для файлов
        files_subq = (
            select(
                func.json_agg(
                    func.json_build_object(
                        "id", FileOrm.id,
                        "name", FileOrm.name,
                        "url", func.concat("/api/v1/files/download/", FileOrm.id)
                    )
                )
            )
            .join(NewsToFileOrm, NewsToFileOrm.file_id == FileOrm.id)
            .where(NewsToFileOrm.news_id == news_id)
            .scalar_subquery()
        )

        # 3. Подзапросы для счетчиков (лайки и комментарии)
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

        # 4. Основной запрос с явным перечислением полей
        query = (
            select(
                NewsOrm.id,
                NewsOrm.title,
                NewsOrm.short_description,
                NewsOrm.content,
                NewsOrm.published_at,
                NewsOrm.is_pinned,
                NewsOrm.mandatory_ack,
                NewsOrm.views_count,
                NewsOrm.status,
                EmployeeOrm.full_name.label("author_name"),
                func.coalesce(likes_count_subq, 0).label("likes_count"),
                func.coalesce(comments_count_subq, 0).label("comments_count"),
                func.coalesce(files_subq, func.json_build_array()).label("files")
            )
            .join(EmployeeOrm, EmployeeOrm.eid == NewsOrm.author_id)
            .where(NewsOrm.id == news_id)
        )

        result = await self.session.execute(query)
        # Используем .mappings(), чтобы соотнести с Pydantic-схемой
        return result.mappings().one_or_none()
    
    async def create_news(self, author_id: int, data: NewsCreateSchema) -> int:
        # 1. Создание записи новости
        new_news = NewsOrm(
            title=data.title,
            short_description=data.short_description,
            content=data.content,
            author_id=author_id,
            is_pinned=data.is_pinned,
            mandatory_ack=data.mandatory_ack
        )
        self.session.add(new_news)
        await self.session.flush()

        # 2. Привязка к категории (NewsToCategoryOrm)
        self.session.add(NewsToCategoryOrm(news_id=new_news.id, category_id=data.category_id))

        # 3. Привязка файлов (NewsToFileOrm)
        if data.file_ids:
            for f_id in data.file_ids:
                self.session.add(NewsToFileOrm(news_id=new_news.id, file_id=f_id))

        # 4. Обработка тегов (Upsert и NewsTagOrm)
        for t_name in data.tag_names:
            tag_stmt = insert(TagOrm).values(name=t_name).on_conflict_do_update(
                index_elements=[TagOrm.name], set_={"name": t_name}
            ).returning(TagOrm.id)
            tag_id = (await self.session.execute(tag_stmt)).scalar()
            self.session.add(NewsTagOrm(news_id=new_news.id, tag_id=tag_id))

        return new_news.id

    async def delete_news(self, news_id: int):
        await self.session.execute(delete(NewsOrm).where(NewsOrm.id == news_id))
        
    
    async def get_all_categories(self):
        stmt = select(CategoryOrm).order_by(CategoryOrm.name)
        result = await self.session.execute(stmt)
        res = result.scalars().all()
        return res

    async def create_category(self, name: str):
        category = CategoryOrm(name=name)
        self.session.add(category)
        await self.session.flush()
        return category

    async def delete_category(self, category_id: int):
        await self.session.execute(delete(CategoryOrm).where(CategoryOrm.id == category_id))
        
    async def update_news_fields(self, news_id: int, update_data: dict):
        await self.session.execute(
            update(NewsOrm).where(NewsOrm.id == news_id).values(**update_data)
        )

    async def update_news_category(self, news_id: int, category_id: int):
        # Удаляем старую привязку и создаем новую
        await self.session.execute(delete(NewsToCategoryOrm).where(NewsToCategoryOrm.news_id == news_id))
        self.session.add(NewsToCategoryOrm(news_id=news_id, category_id=category_id))

    async def update_news_tags(self, news_id: int, tag_names: list[str]):
        # 1. Удаляем старые связи
        await self.session.execute(delete(NewsTagOrm).where(NewsTagOrm.news_id == news_id))
        
        # 2. Привязываем новые теги
        for t_name in tag_names:
            tag_stmt = insert(TagOrm).values(name=t_name).on_conflict_do_update(
                index_elements=[TagOrm.name], set_={"name": t_name}
            ).returning(TagOrm.id)
            tag_id = (await self.session.execute(tag_stmt)).scalar()
            self.session.add(NewsTagOrm(news_id=news_id, tag_id=tag_id))

    async def update_news_files(self, news_id: int, file_ids: list[int]):
        # Удаляем старые связи с файлами и записываем новые
        await self.session.execute(delete(NewsToFileOrm).where(NewsToFileOrm.news_id == news_id))
        for f_id in file_ids:
            self.session.add(NewsToFileOrm(news_id=news_id, file_id=f_id))