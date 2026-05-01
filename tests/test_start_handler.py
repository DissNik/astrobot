from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from bot.db.connection import connect
from bot.db.migrations import migrate
from bot.domain.enums import ObservingProfile
from bot.domain.models import User
from bot.handlers.start import start_command
from bot.repositories.users import UserRepository


class FakeUser:
    def __init__(self, user_id: int) -> None:
        self.id = user_id


class FakeMessage:
    def __init__(self, user_id: int) -> None:
        self.from_user = FakeUser(user_id)
        self.answers: list[tuple[str, object | None]] = []

    async def answer(self, text: str, reply_markup=None) -> None:  # noqa: ANN001
        self.answers.append((text, reply_markup))


def _users(tmp_path: Path) -> UserRepository:
    connection = connect(tmp_path / "astrobot.sqlite3")
    migrate(connection)
    return UserRepository(connection)


@pytest.mark.asyncio
async def test_start_command_uses_saved_user_language(tmp_path: Path) -> None:
    users = _users(tmp_path)
    users.upsert(
        User(
            telegram_id=100,
            timezone="UTC",
            language="ru",
            forecast_days=3,
            observing_profile=ObservingProfile.DEEP_SKY,
            score_threshold=60,
            created_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
        )
    )
    users.connection.commit()
    message = FakeMessage(100)

    await start_command(message, users=users)  # type: ignore[arg-type]

    text, keyboard = message.answers[0]
    assert text == "Привет! Я помогу выбрать лучшее время для астрономической поездки."
    labels = [button.text for row in keyboard.keyboard for button in row]
    assert "🔭 Прогноз" in labels
    assert "⚙️ Настройки" in labels
