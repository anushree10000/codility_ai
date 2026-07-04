from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "job_scheduler"

    # JWT
    JWT_SECRET_KEY: str = "change-this-to-a-random-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Worker
    WORKER_CONCURRENCY: int = 5
    WORKER_POLL_INTERVAL: float = 1.0
    WORKER_HEARTBEAT_INTERVAL: int = 30
    WORKER_STALE_THRESHOLD: int = 90

    @property
    def database_url(self) -> str:
        from urllib.parse import quote_plus
        encoded_password = quote_plus(self.DB_PASSWORD) if self.DB_PASSWORD else ""
        return (
            f"mysql+asyncmy://{self.DB_USER}:{encoded_password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def database_url_sync(self) -> str:
        """Sync URL for create_all() and tests."""
        from urllib.parse import quote_plus
        encoded_password = quote_plus(self.DB_PASSWORD) if self.DB_PASSWORD else ""
        return (
            f"mysql+pymysql://{self.DB_USER}:{encoded_password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
