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
            f"{self.DB_PORT}/{self.DB_NAME}"
        )


class Settings(BaseSettings):
    load_dotenv()

    STATIC_PATH: str = os.environ.get("STATIC_PATH")
    ELASTICSEARCH_HOST: str = os.getenv(
        "ELASTICSEARCH_HOST", "http://localhost:9200"
    )
    ELASTICSEARCH_INDEX_NAME: str = os.getenv(
        "ELASTICSEARCH_INDEX_NAME", "employee"
    )
    KEYCLOAK_SERVER_URL: str = os.getenv(
        "KEYCLOAK_SERVER_URL", "http://localhost:8080/auth"
    )
    KEYCLOAK_REALM: str = os.getenv("KEYCLOAK_REALM", "bank-realm")
    KEYCLOAK_CLIENT_ID: str = os.getenv("KEYCLOAK_CLIENT_ID", "bank-client")
    KEYCLOAK_CLIENT_SECRET: str = os.getenv("KEYCLOAK_CLIENT_SECRET", "")
    KEYCLOAK_PUBLIC_KEY: str = os.getenv("KEYCLOAK_PUBLIC_KEY", "")

    API_KEY_1C: str = os.getenv("API_KEY_1C", "")

    SCHEDULED_NEWS_CHECK_INTERVAL: int = int(
        os.getenv("SCHEDULED_NEWS_CHECK_INTERVAL", "60")
    )
    
    THESIS_BASE_URL: str = os.getenv(
        "THESIS_BASE_URL", "https://thesis.corporate.ru"
    )
    THESIS_CLIENT_ID: str = os.getenv("THESIS_CLIENT_ID", "")
    THESIS_CLIENT_SECRET: str = os.getenv("THESIS_CLIENT_SECRET", "")
    THESIS_JWT_SECRET: str = os.getenv("THESIS_JWT_SECRET", "")
    
    BAND_BOT_URL: str = os.getenv("BAND_BOT_URL", "")
    BAND_BOT_TOKEN: str = os.getenv("BAND_BOT_TOKEN", "")
    BAND_BOT_TIMEOUT: int = int(os.getenv("BAND_BOT_TIMEOUT", "30"))


def get_settings():
    return Settings()


def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()
