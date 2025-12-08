import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class DatabaseSettings:
    def __init__(self):

        self.DB_USER = os.getenv("DB_USER", "postgres")
        self.DB_PASS = os.getenv("DB_PASS", "postgres")
        self.DB_HOST = os.getenv("DB_HOST", "localhost")
        self.DB_PORT = os.getenv("DB_PORT", "5432")
        self.DB_NAME = os.getenv("DB_NAME", "postgres")

    @property
    def url(self) -> str:
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:"
            f"{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def async_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:"
            f"{self.DB_PORT}/{self.DB_NAME}?async_fallback=True"
        )


class Settings(BaseSettings):
    load_dotenv()

    STATIC_PATH: str = os.environ.get("STATIC_PATH")


def get_settings():
    return Settings()


def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()
