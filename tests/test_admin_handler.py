import pytest

from bot.handlers.admin import is_owner, stats_command


def test_is_owner_allows_configured_owner() -> None:
    assert is_owner(user_id=42, owner_ids=(42, 100)) is True
    assert is_owner(user_id=100, owner_ids=(42, 100)) is True


def test_is_owner_rejects_other_users() -> None:
    assert is_owner(user_id=200, owner_ids=(42, 100)) is False


class FakeUser:
    def __init__(self, user_id: int) -> None:
        self.id = user_id


class FakeMessage:
    def __init__(self, user_id: int) -> None:
        self.from_user = FakeUser(user_id)
        self.answers: list[str] = []

    async def answer(self, text: str) -> None:
        self.answers.append(text)


class FakeStats:
    def summary(self) -> dict[str, int]:
        return {"users": 2, "locations": 3, "active_subscriptions": 1}


@pytest.mark.asyncio
async def test_stats_command_rejects_non_owner() -> None:
    message = FakeMessage(user_id=100)

    await stats_command(message, owner_telegram_ids=(42,), stats=FakeStats())  # type: ignore[arg-type]

    assert message.answers == ["Команда доступна только владельцу бота."]


@pytest.mark.asyncio
async def test_stats_command_formats_owner_stats() -> None:
    message = FakeMessage(user_id=100)

    await stats_command(message, owner_telegram_ids=(42, 100), stats=FakeStats())  # type: ignore[arg-type]

    assert message.answers == [
        "Статистика бота:\nПользователи: 2\nЛокации: 3\nАктивные подписки: 1"
    ]
