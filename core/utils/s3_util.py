from contextlib import asynccontextmanager
from typing import AsyncGenerator

from aiobotocore.session import get_session
from types_aiobotocore_s3 import S3Client

from core.config.settings import get_settings


@asynccontextmanager
async def get_s3_client() -> AsyncGenerator[S3Client, None]:
    settings = get_settings()
    session = get_session()
    async with session.create_client(
        "s3",
        endpoint_url=settings.MINIO_ENDPOINT,
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
    ) as client:
        yield client


async def get_s3_dep() -> AsyncGenerator[S3Client, None]:
    async with get_s3_client() as client:
        yield client
