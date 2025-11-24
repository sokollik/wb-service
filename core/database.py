# core/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from core.config.settings import get_database_settings

# Получаем настройки
db_settings = get_database_settings()

print(f"Database URL: {db_settings.async_url}")  # Для дебага

engine = create_async_engine(
    db_settings.async_url,
    echo=True,
    poolclass=NullPool,
    # Критически важные параметры для asyncpg + PostgreSQL
    connect_args={
        "server_settings": {
            "jit": "off",  # Отключаем JIT для стабильности
            "statement_timeout": "30000",  # 30 секунд таймаут
        }
    }
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()