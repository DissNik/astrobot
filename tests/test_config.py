from pathlib import Path

import pytest
from pydantic import ValidationError

from bot.config import Settings


def test_settings_load_required_values(tmp_path: Path) -> None:
    settings = Settings(
        telegram_bot_token="123:abc",
        owner_telegram_id=42,
        database_path=tmp_path / "astrobot.sqlite3",
        log_level="DEBUG",
    )

    assert settings.telegram_bot_token == "123:abc"
    assert settings.owner_telegram_id == 42
    assert settings.database_path == tmp_path / "astrobot.sqlite3"
    assert settings.log_level == "DEBUG"


def test_settings_default_values(tmp_path: Path) -> None:
    settings = Settings(
        telegram_bot_token="123:abc",
        owner_telegram_id=42,
        database_path=tmp_path / "astrobot.sqlite3",
    )

    assert settings.log_level == "INFO"


def test_settings_rejects_empty_token(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        Settings(
            telegram_bot_token="",
            owner_telegram_id=42,
            database_path=tmp_path / "astrobot.sqlite3",
        )
