from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import AsyncAdaptedQueuePool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config.settings import get_database_settings

engine = create_async_engine(
    get_database_settings().async_url,
)

session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session = session_maker()
    async with session.begin():
        yield session
    await session.close()


async def get_session_obj() -> AsyncGenerator[AsyncSession, None]:
    session = session_maker()
    async with session.begin():
        yield session
    await session.close()
