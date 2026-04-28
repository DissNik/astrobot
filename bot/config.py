from pathlib import Path
from typing import Annotated, Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )

    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    owner_telegram_ids: Annotated[tuple[int, ...], NoDecode] = Field(alias="OWNER_TELEGRAM_IDS")
    database_path: Path = Field(alias="DATABASE_PATH")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @field_validator("telegram_bot_token")
    @classmethod
    def token_must_not_be_empty(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("TELEGRAM_BOT_TOKEN must not be empty")
        return normalized

    @field_validator("owner_telegram_ids", mode="before")
    @classmethod
    def parse_owner_ids(cls, value: Any) -> tuple[int, ...]:
        if isinstance(value, int):
            owner_ids = (value,)
        elif isinstance(value, str):
            parts = [part.strip() for part in value.replace(";", ",").split(",")]
            owner_ids = tuple(int(part) for part in parts if part)
        else:
            owner_ids = tuple(value)

        if not owner_ids:
            raise ValueError("OWNER_TELEGRAM_IDS must contain at least one id")
        return owner_ids

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        normalized = value.strip().upper()
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if normalized not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(sorted(allowed))}")
        return normalized
