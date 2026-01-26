import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    secret_key: str
    database_url: str = "sqlite:///./habit_tracker.db"
    algorithm: str = "HS256"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    if os.getenv("ENVIRONMENT") == "testing":
        return Settings(_env_file=".env.test")
    return Settings()
