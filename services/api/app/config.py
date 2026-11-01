"""API configuration, read from environment variables."""
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    database_url: str
    inference_url: str = "http://inference:8001"
    cors_origins: str = "http://localhost:3000"
    inference_connect_timeout: float = Field(default=3.0, gt=0, le=30)
    inference_read_timeout: float = Field(default=30.0, gt=0, le=300)
    inference_max_retries: int = Field(default=2, ge=0, le=5)
    inference_max_concurrency: int = Field(default=4, ge=1, le=64)

    @field_validator("cors_origins")
    @classmethod
    def reject_wildcard_origin(cls, value: str) -> str:
        if any(origin.strip() == "*" for origin in value.split(",")):
            raise ValueError("CORS_ORIGINS must list explicit origins; '*' is not allowed.")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
