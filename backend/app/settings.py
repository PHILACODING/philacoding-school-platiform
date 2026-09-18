from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://school_app:change-me@localhost:5432/school_platform"
    api_env: str = "development"
    cors_origins: str = "http://127.0.0.1:5500,http://localhost:5500"
    secret_key: str = "replace-this-development-secret"
    default_school_slug: str = "siphesihle-high-school"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
