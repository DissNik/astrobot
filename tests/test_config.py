from pathlib import Path

import pytest
from pydantic import ValidationError

from bot.config import Settings


def test_settings_load_required_values(tmp_path: Path) -> None:
    settings = Settings(
        telegram_bot_token="123:abc",
        owner_telegram_ids=(42, 100),
        database_path=tmp_path / "astrobot.sqlite3",
        log_level="DEBUG",
    )

    assert settings.telegram_bot_token == "123:abc"
    assert settings.owner_telegram_ids == (42, 100)
    assert settings.database_path == tmp_path / "astrobot.sqlite3"
    assert settings.log_level == "DEBUG"


def test_settings_default_values(tmp_path: Path) -> None:
    settings = Settings(
        telegram_bot_token="123:abc",
        owner_telegram_ids=(42,),
        database_path=tmp_path / "astrobot.sqlite3",
    )

    assert settings.log_level == "INFO"


def test_settings_loads_values_from_env_file(tmp_path: Path) -> None:
    database_path = tmp_path / "astrobot.sqlite3"
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "TELEGRAM_BOT_TOKEN=123:abc",
                "OWNER_TELEGRAM_IDS=42, 100",
                f"DATABASE_PATH={database_path}",
                "LOG_LEVEL=debug",
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)

    assert settings.telegram_bot_token == "123:abc"
    assert settings.owner_telegram_ids == (42, 100)
    assert settings.database_path == database_path
    assert settings.log_level == "DEBUG"


def test_settings_normalizes_whitespace(tmp_path: Path) -> None:
    settings = Settings(
        telegram_bot_token=" 123:abc ",
        owner_telegram_ids=(42,),
        database_path=tmp_path / "astrobot.sqlite3",
        log_level=" info ",
    )

    assert settings.telegram_bot_token == "123:abc"
    assert settings.log_level == "INFO"


def test_settings_rejects_empty_token(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        Settings(
            telegram_bot_token="",
            owner_telegram_ids=(42,),
            database_path=tmp_path / "astrobot.sqlite3",
        )


def test_settings_rejects_empty_owner_ids(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        Settings(
            telegram_bot_token="123:abc",
            owner_telegram_ids=(),
            database_path=tmp_path / "astrobot.sqlite3",
        )
