import os
from functools import lru_cache

from pydantic import computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"

    secret_key: str
    algorithm: str = "HS256"

    postgres_user: str | None = None
    postgres_password: str | None = None
    postgres_db: str | None = None
    postgres_host: str | None = None
    postgres_port: int = 5432

    _database_url: str | None = None

    ollama_base_url: str | None = None

    langchain_tracing: bool = False
    langchain_endpoint: str | None = None
    langchain_api_key: str | None = None
    langchain_project: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def verify_required_settings(self) -> Settings:
        if self.environment != "testing":
            if not self.ollama_base_url:
                raise ValueError(
                    "OLLAMA_BASE_URL is required in non-testing environments."
                )
            if self.langchain_tracing and (
                not self.langchain_endpoint
                or not self.langchain_api_key
                or not self.langchain_project
            ):
                raise ValueError(
                    "LANGCHAIN_ENDPOINT, LANGCHAIN_API_KEY and LANGCHAIN_PROJECT are "
                    "required when LANGCHAIN_TRACING is enabled."
                )
        return self

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
            "No database configuration! Set _DATABASE_URL or POSTGRES_* variable set."
        )


@lru_cache
def get_settings() -> Settings:
    if os.getenv("ENVIRONMENT") == "testing":
        return Settings(_env_file=".env.test")
    return Settings()
