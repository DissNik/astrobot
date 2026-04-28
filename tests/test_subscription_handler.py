from pathlib import Path

import pytest

from bot.db.connection import connect
from bot.db.migrations import migrate
from bot.handlers.subscription import disable_subscription_callback, enable_subscription_callback
from bot.repositories.subscriptions import SubscriptionRepository
from bot.repositories.users import UserRepository


class FakeUser:
    def __init__(self, user_id: int) -> None:
        self.id = user_id


class FakeMessage:
    def __init__(self, user_id: int) -> None:
        self.from_user = FakeUser(user_id)
        self.answers: list[str] = []

    async def answer(self, text: str, reply_markup=None) -> None:  # noqa: ANN001
        self.answers.append(text)


class FakeCallback:
    def __init__(self, user_id: int, message: FakeMessage | None = None) -> None:
        self.from_user = FakeUser(user_id)
        self.message = message
        self.answers: list[tuple[str | None, bool | None]] = []

    async def answer(self, text: str | None = None, show_alert: bool | None = None) -> None:
        self.answers.append((text, show_alert))


def _repositories(tmp_path: Path) -> tuple[UserRepository, SubscriptionRepository]:
    connection = connect(tmp_path / "astrobot.sqlite3")
    migrate(connection)
    return UserRepository(connection), SubscriptionRepository(connection)


@pytest.mark.asyncio
async def test_enable_subscription_callback_creates_enabled_subscription(tmp_path: Path) -> None:
    users, subscriptions = _repositories(tmp_path)
    message = FakeMessage(user_id=100)
    callback = FakeCallback(user_id=100, message=message)

    await enable_subscription_callback(
        callback,
        users=users,
        subscriptions=subscriptions,
        connection=subscriptions.connection,
    )  # type: ignore[arg-type]

    subscription = subscriptions.get(100)
    assert subscription is not None
    assert subscription.enabled is True
    assert subscription.forecast_days == 3
    assert subscription.score_threshold == 60
    assert message.answers == [
        "Рассылка включена. По умолчанию отправляю ежедневный дайджест в 20:00 UTC."
    ]


@pytest.mark.asyncio
async def test_disable_subscription_callback_disables_existing_subscription(tmp_path: Path) -> None:
    users, subscriptions = _repositories(tmp_path)
    callback = FakeCallback(user_id=100, message=FakeMessage(user_id=100))

    await enable_subscription_callback(
        callback,
        users=users,
        subscriptions=subscriptions,
        connection=subscriptions.connection,
    )  # type: ignore[arg-type]
    await disable_subscription_callback(
        callback,
        users=users,
        subscriptions=subscriptions,
        connection=subscriptions.connection,
    )  # type: ignore[arg-type]

    subscription = subscriptions.get(100)
    assert subscription is not None
    assert subscription.enabled is False
