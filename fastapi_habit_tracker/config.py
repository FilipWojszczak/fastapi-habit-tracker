import os
from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    secret_key: str
    algorithm: str = "HS256"

    postgres_user: str | None = None
    postgres_password: str | None = None
    postgres_db: str | None = None
    postgres_host: str | None = None
    postgres_port: int = 5432

    _database_url: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @computed_field
    @property
    def database_url(self) -> str:
        if self._database_url:
            return self._database_url
        if all(
            [
                self.postgres_user,
                self.postgres_password,
                self.postgres_db,
                self.postgres_host,
            ]
        ):
            return (
                f"postgresql+psycopg://{self.postgres_user}:"
                f"{self.postgres_password}@{self.postgres_host}:"
                f"{self.postgres_port}/{self.postgres_db}"
            )
        raise ValueError(
            "No database configuration! Set DATABASE_URL or POSTGRES_* variable set."
        )


@lru_cache
def get_settings() -> Settings:
    if os.getenv("ENVIRONMENT") == "testing":
        return Settings(_env_file=".env.test")
    return Settings()
