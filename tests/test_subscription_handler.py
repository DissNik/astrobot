from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from bot.db.connection import connect
from bot.db.migrations import migrate
from bot.domain.enums import ObservingProfile, SubscriptionMode
from bot.domain.models import Subscription, User
from bot.handlers.subscription import (
    disable_subscription_callback,
    enable_subscription_callback,
    subscription_callback,
)
from bot.repositories.subscriptions import SubscriptionRepository
from bot.repositories.users import UserRepository
from bot.services.subscription_service import last_sent_on_for_enabled_subscription


class FakeUser:
    def __init__(self, user_id: int) -> None:
        self.id = user_id


class FakeMessage:
    def __init__(self, user_id: int) -> None:
        self.from_user = FakeUser(user_id)
        self.answers: list[str] = []
        self.edits: list[tuple[str, object | None]] = []
        self.parse_modes: list[str | None] = []

    async def answer(self, text: str, reply_markup=None, parse_mode: str | None = None) -> None:  # noqa: ANN001
        self.answers.append(text)
        self.parse_modes.append(parse_mode)

    async def edit_text(self, text: str, reply_markup=None, parse_mode: str | None = None) -> None:  # noqa: ANN001
        self.edits.append((text, reply_markup))
        self.parse_modes.append(parse_mode)


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
    assert message.answers == []
    assert message.edits[0][0] == (
        "<b>📬 Alerts</b>\n"
        "____________\n\n"
        "🔔 Subscription: Enabled\n"
        "🕘 Time: 20:00 UTC\n"
        "📬 Mode: Daily digest\n"
        "⭐ Threshold: 60/100"
    )
    assert message.parse_modes[0] == "HTML"
    keyboard = message.edits[0][1]
    labels_by_callback = {
        button.callback_data: button.text
        for row in keyboard.inline_keyboard
        for button in row
    }

    assert labels_by_callback["subscription:enable"] == "✅ Enabled"
    assert labels_by_callback["subscription:disable"] == "Disabled"
    assert labels_by_callback["settings:open"] == "⚙️ Settings"


@pytest.mark.asyncio
async def test_enable_subscription_callback_reports_configured_time_and_timezone(
    tmp_path: Path,
) -> None:
    users, subscriptions = _repositories(tmp_path)
    now = datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC"))
    users.upsert(
        User(
            telegram_id=100,
            timezone="UTC",
            language="ru",
            forecast_days=3,
            observing_profile=ObservingProfile.DEEP_SKY,
            score_threshold=60,
            created_at=now,
        )
    )
    subscriptions.upsert(
        Subscription(
            user_id=100,
            enabled=False,
            mode=SubscriptionMode.DAILY_DIGEST,
            send_time_local=time(9, 3),
            forecast_days=3,
            observing_profile=ObservingProfile.DEEP_SKY,
            score_threshold=60,
            updated_at=now,
        )
    )
    users.connection.commit()
    message = FakeMessage(user_id=100)
    callback = FakeCallback(user_id=100, message=message)

    await enable_subscription_callback(
        callback,
        users=users,
        subscriptions=subscriptions,
        connection=subscriptions.connection,
    )  # type: ignore[arg-type]

    assert subscriptions.get(100).send_time_local == time(9, 3)
    assert message.answers == []
    assert message.edits[0][0] == (
        "<b>📬 Рассылка</b>\n"
        "____________\n\n"
        "🔔 Рассылка: Включена\n"
        "🕘 Время: 09:03 UTC\n"
        "📬 Режим: Ежедневный дайджест\n"
        "⭐ Порог: 60/100"
    )


def test_enable_subscription_after_configured_time_skips_current_local_day() -> None:
    user = User(
        telegram_id=100,
        timezone="Europe/Moscow",
        language="ru",
        forecast_days=3,
        observing_profile=ObservingProfile.DEEP_SKY,
        score_threshold=60,
        created_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
    )
    subscription = Subscription(
        user_id=100,
        enabled=False,
        mode=SubscriptionMode.DAILY_DIGEST,
        send_time_local=time(12, 52),
        forecast_days=3,
        observing_profile=ObservingProfile.DEEP_SKY,
        score_threshold=60,
        updated_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
    )

    last_sent_on = last_sent_on_for_enabled_subscription(
        subscription,
        user,
        now_utc=datetime(2026, 4, 26, 12, 0, tzinfo=ZoneInfo("UTC")),
    )

    assert last_sent_on == date(2026, 4, 26)


def test_enable_subscription_before_configured_time_keeps_subscription_due_today() -> None:
    user = User(
        telegram_id=100,
        timezone="Europe/Moscow",
        language="ru",
        forecast_days=3,
        observing_profile=ObservingProfile.DEEP_SKY,
        score_threshold=60,
        created_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
    )
    subscription = Subscription(
        user_id=100,
        enabled=False,
        mode=SubscriptionMode.DAILY_DIGEST,
        send_time_local=time(12, 52),
        forecast_days=3,
        observing_profile=ObservingProfile.DEEP_SKY,
        score_threshold=60,
        updated_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
    )

    last_sent_on = last_sent_on_for_enabled_subscription(
        subscription,
        user,
        now_utc=datetime(2026, 4, 26, 9, 0, tzinfo=ZoneInfo("UTC")),
    )

    assert last_sent_on is None


@pytest.mark.asyncio
async def test_subscription_callback_edits_current_message(tmp_path: Path) -> None:
    users, subscriptions = _repositories(tmp_path)
    message = FakeMessage(user_id=100)
    callback = FakeCallback(user_id=100, message=message)

    await subscription_callback(callback, users=users, subscriptions=subscriptions)  # type: ignore[arg-type]

    assert message.answers == []
    assert message.edits[0][0] == (
        "<b>📬 Alerts</b>\n"
        "____________\n\n"
        "🔔 Subscription: Disabled\n"
        "🕘 Time: 20:00 UTC\n"
        "📬 Mode: Daily digest\n"
        "⭐ Threshold: 60/100"
    )
    assert callback.answers == [(None, None)]


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
    assert callback.message.answers == []
    assert callback.message.edits[-1][0] == (
        "<b>📬 Alerts</b>\n"
        "____________\n\n"
        "🔔 Subscription: Disabled\n"
        "🕘 Time: 20:00 UTC\n"
        "📬 Mode: Daily digest\n"
        "⭐ Threshold: 60/100"
    )
