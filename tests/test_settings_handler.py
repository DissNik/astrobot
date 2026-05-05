from datetime import UTC, datetime, time
from pathlib import Path

import pytest
from aiogram.exceptions import TelegramBadRequest

from bot.db.connection import connect
from bot.db.migrations import migrate
from bot.domain.enums import ObservingProfile, SubscriptionMode
from bot.domain.models import User
from bot.handlers.settings import (
    settings_command,
    settings_time_callback,
    settings_time_message,
    update_forecast_days_callback,
    update_language_callback,
    update_profile_callback,
    update_subscription_mode_callback,
    update_threshold_callback,
)
from bot.repositories.subscriptions import SubscriptionRepository
from bot.repositories.users import UserRepository


class FakeUser:
    def __init__(self, user_id: int) -> None:
        self.id = user_id


class FakeSentMessage:
    def __init__(self) -> None:
        self.deleted = False

    async def delete(self) -> None:
        self.deleted = True


class FakeMessage:
    def __init__(
        self,
        user_id: int,
        text: str | None = None,
        edit_error: TelegramBadRequest | None = None,
    ) -> None:
        self.from_user = FakeUser(user_id)
        self.text = text
        self.edit_error = edit_error
        self.answers: list[tuple[str, object | None]] = []
        self.edits: list[tuple[str, object | None]] = []
        self.sent_messages: list[FakeSentMessage] = []

    async def answer(
        self,
        text: str,
        reply_markup=None,
        parse_mode: str | None = None,
    ) -> FakeSentMessage:  # noqa: ANN001
        self.answers.append((text, reply_markup))
        sent_message = FakeSentMessage()
        self.sent_messages.append(sent_message)
        return sent_message

    async def edit_text(self, text: str, reply_markup=None, parse_mode: str | None = None) -> None:  # noqa: ANN001
        if self.edit_error is not None:
            raise self.edit_error
        self.edits.append((text, reply_markup))


class FakeCallback:
    def __init__(self, user_id: int, data: str, message: FakeMessage | None = None) -> None:
        self.from_user = FakeUser(user_id)
        self.data = data
        self.message = message
        self.answers: list[tuple[str | None, bool | None]] = []

    async def answer(self, text: str | None = None, show_alert: bool | None = None) -> None:
        self.answers.append((text, show_alert))


class FakeState:
    def __init__(self) -> None:
        self.state = None
        self.cleared = False

    async def set_state(self, state) -> None:  # noqa: ANN001
        self.state = state

    async def clear(self) -> None:
        self.state = None
        self.cleared = True


def _repositories(tmp_path: Path) -> tuple[UserRepository, SubscriptionRepository]:
    connection = connect(tmp_path / "astrobot.sqlite3")
    migrate(connection)
    return UserRepository(connection), SubscriptionRepository(connection)


@pytest.mark.asyncio
async def test_settings_command_shows_edit_buttons(tmp_path: Path) -> None:
    users, subscriptions = _repositories(tmp_path)
    message = FakeMessage(user_id=100)

    await settings_command(message, users=users, subscriptions=subscriptions)  # type: ignore[arg-type]

    text, keyboard = message.answers[0]
    labels = [button.text for row in keyboard.inline_keyboard for button in row]
    assert "<b>⚙️ Profile and subscription settings</b>" in text
    assert "____________\n\n" in text
    assert "✅ 3 nights" in labels
    assert "5 nights" in labels
    assert "✅ Deep-sky" in labels
    assert "Good conditions only" in labels
    assert "✅ English" in labels
    assert "Русский" in labels
    assert "Notification time" in labels


@pytest.mark.asyncio
async def test_update_language_saves_selected_language(tmp_path: Path) -> None:
    users, subscriptions = _repositories(tmp_path)
    callback = FakeCallback(100, "settings:language:ru", FakeMessage(100))

    await update_language_callback(
        callback,
        users=users,
        subscriptions=subscriptions,
        connection=users.connection,
    )  # type: ignore[arg-type]

    assert users.get(100).language == "ru"
    assert "<b>⚙️ Настройки профиля и рассылки</b>" in callback.message.edits[0][0]


@pytest.mark.asyncio
async def test_update_language_does_not_send_main_menu_message(tmp_path: Path) -> None:
    users, subscriptions = _repositories(tmp_path)
    callback = FakeCallback(100, "settings:language:ru", FakeMessage(100))

    await update_language_callback(
        callback,
        users=users,
        subscriptions=subscriptions,
        connection=users.connection,
    )  # type: ignore[arg-type]

    assert len(callback.message.answers) == 1
    text, keyboard = callback.message.answers[0]
    labels = [button.text for row in keyboard.keyboard for button in row]
    assert text == "Установлен русский язык."
    assert "🔭 Прогноз" in labels
    assert "⚙️ Настройки" in labels
    assert callback.message.sent_messages[0].deleted is False


@pytest.mark.asyncio
async def test_update_forecast_days_saves_user_and_subscription(tmp_path: Path) -> None:
    users, subscriptions = _repositories(tmp_path)
    callback = FakeCallback(100, "settings:days:5", FakeMessage(100))

    await update_forecast_days_callback(
        callback,
        users=users,
        subscriptions=subscriptions,
        connection=users.connection,
    )  # type: ignore[arg-type]

    assert users.get(100).forecast_days == 5
    assert subscriptions.get(100).forecast_days == 5


@pytest.mark.asyncio
async def test_update_forecast_days_edits_settings_message_with_visual_summary(
    tmp_path: Path,
) -> None:
    users, subscriptions = _repositories(tmp_path)
    callback = FakeCallback(100, "settings:days:5", FakeMessage(100))

    await update_forecast_days_callback(
        callback,
        users=users,
        subscriptions=subscriptions,
        connection=users.connection,
    )  # type: ignore[arg-type]

    text, keyboard = callback.message.edits[0]
    assert callback.message.answers == []
    labels = [button.text for row in keyboard.inline_keyboard for button in row]
    assert text == (
        "<b>⚙️ Profile and subscription settings</b>\n"
        "____________\n\n"
        "🌙 Forecast: 5 nights\n"
        "🔭 Profile: Deep-sky\n"
        "🔔 Subscription: disabled\n"
        "🕘 Time: 20:00 UTC\n"
        "📬 Mode: Daily digest\n"
        "⭐ Threshold: 60/100"
    )
    assert keyboard.inline_keyboard[0][0].callback_data == "settings:days:3"
    assert "✅ 5 nights" in labels
    assert "3 nights" in labels


@pytest.mark.asyncio
async def test_update_forecast_days_ignores_unchanged_settings_message(
    tmp_path: Path,
) -> None:
    users, subscriptions = _repositories(tmp_path)
    message = FakeMessage(
        100,
        edit_error=TelegramBadRequest(method=None, message="Bad Request: message is not modified"),
    )
    callback = FakeCallback(100, "settings:days:3", message)

    await update_forecast_days_callback(
        callback,
        users=users,
        subscriptions=subscriptions,
        connection=users.connection,
    )  # type: ignore[arg-type]

    assert message.answers == []
    assert callback.answers == [(None, None)]


@pytest.mark.asyncio
async def test_update_language_edits_settings_without_status_prefix(tmp_path: Path) -> None:
    users, subscriptions = _repositories(tmp_path)
    callback = FakeCallback(100, "settings:language:ru", FakeMessage(100))

    await update_language_callback(
        callback,
        users=users,
        subscriptions=subscriptions,
        connection=users.connection,
    )  # type: ignore[arg-type]

    assert callback.message.edits[0][0].startswith("<b>⚙️ Настройки профиля и рассылки</b>")
    assert "Язык обновлен" not in callback.message.edits[0][0]


@pytest.mark.asyncio
async def test_update_profile_saves_user_and_subscription(tmp_path: Path) -> None:
    users, subscriptions = _repositories(tmp_path)
    callback = FakeCallback(100, "settings:profile:planetary_lunar", FakeMessage(100))

    await update_profile_callback(
        callback,
        users=users,
        subscriptions=subscriptions,
        connection=users.connection,
    )  # type: ignore[arg-type]

    assert users.get(100).observing_profile is ObservingProfile.PLANETARY_LUNAR
    assert subscriptions.get(100).observing_profile is ObservingProfile.PLANETARY_LUNAR


@pytest.mark.asyncio
async def test_update_threshold_saves_user_and_subscription(tmp_path: Path) -> None:
    users, subscriptions = _repositories(tmp_path)
    callback = FakeCallback(100, "settings:threshold:70", FakeMessage(100))

    await update_threshold_callback(
        callback,
        users=users,
        subscriptions=subscriptions,
        connection=users.connection,
    )  # type: ignore[arg-type]

    assert users.get(100).score_threshold == 70
    assert subscriptions.get(100).score_threshold == 70


@pytest.mark.asyncio
async def test_update_subscription_mode_saves_subscription(tmp_path: Path) -> None:
    users, subscriptions = _repositories(tmp_path)
    callback = FakeCallback(100, "settings:mode:good_conditions_only", FakeMessage(100))

    await update_subscription_mode_callback(
        callback,
        users=users,
        subscriptions=subscriptions,
        connection=users.connection,
    )  # type: ignore[arg-type]

    assert subscriptions.get(100).mode is SubscriptionMode.GOOD_CONDITIONS_ONLY


@pytest.mark.asyncio
async def test_update_subscription_time_saves_subscription_and_timezone(tmp_path: Path) -> None:
    users, subscriptions = _repositories(tmp_path)
    state = FakeState()
    callback = FakeCallback(100, "settings:time", FakeMessage(100))

    await settings_time_callback(callback, state, users=users)  # type: ignore[arg-type]
    await settings_time_message(
        FakeMessage(100, text="21:30 Europe/Moscow"),
        state,  # type: ignore[arg-type]
        users=users,
        subscriptions=subscriptions,
        connection=users.connection,
    )

    assert state.cleared is True
    assert users.get(100).timezone == "Europe/Moscow"
    assert subscriptions.get(100).send_time_local == time(21, 30)
    prompt_text, keyboard = callback.message.answers[0]
    labels = [button.text for row in keyboard.keyboard for button in row]
    assert prompt_text == (
        "Enter notification time, for example 21:30. You can also add a timezone: "
        "21:30 Europe/Moscow or 21:30 +5."
    )
    assert "🔭 Forecast" in labels
    assert "⚙️ Settings" in labels


@pytest.mark.asyncio
async def test_update_subscription_time_without_timezone_uses_current_user_timezone(
    tmp_path: Path,
) -> None:
    users, subscriptions = _repositories(tmp_path)
    state = FakeState()
    users.upsert(
        User(
            telegram_id=100,
            timezone="Asia/Yekaterinburg",
            language="ru",
            forecast_days=3,
            observing_profile=ObservingProfile.DEEP_SKY,
            score_threshold=60,
            created_at=datetime(2026, 4, 26, tzinfo=UTC),
        )
    )
    users.connection.commit()

    await settings_time_message(
        FakeMessage(100, text="21:30"),
        state,  # type: ignore[arg-type]
        users=users,
        subscriptions=subscriptions,
        connection=users.connection,
    )

    assert state.cleared is True
    assert users.get(100).timezone == "Asia/Yekaterinburg"
    assert subscriptions.get(100).send_time_local == time(21, 30)


@pytest.mark.asyncio
async def test_update_subscription_time_without_timezone_uses_utc_for_new_user(
    tmp_path: Path,
) -> None:
    users, subscriptions = _repositories(tmp_path)
    state = FakeState()

    await settings_time_message(
        FakeMessage(100, text="21:30"),
        state,  # type: ignore[arg-type]
        users=users,
        subscriptions=subscriptions,
        connection=users.connection,
    )

    assert state.cleared is True
    assert users.get(100).timezone == "UTC"
    assert subscriptions.get(100).send_time_local == time(21, 30)


@pytest.mark.asyncio
async def test_update_subscription_time_accepts_short_utc_offset(tmp_path: Path) -> None:
    users, subscriptions = _repositories(tmp_path)
    state = FakeState()

    await settings_time_message(
        FakeMessage(100, text="21:30 +5"),
        state,  # type: ignore[arg-type]
        users=users,
        subscriptions=subscriptions,
        connection=users.connection,
    )

    assert state.cleared is True
    assert users.get(100).timezone == "UTC+05:00"
    assert subscriptions.get(100).send_time_local == time(21, 30)


@pytest.mark.asyncio
async def test_update_subscription_time_accepts_prefixed_utc_offset(tmp_path: Path) -> None:
    users, subscriptions = _repositories(tmp_path)
    state = FakeState()

    await settings_time_message(
        FakeMessage(100, text="21:30 UTC+5"),
        state,  # type: ignore[arg-type]
        users=users,
        subscriptions=subscriptions,
        connection=users.connection,
    )

    assert state.cleared is True
    assert users.get(100).timezone == "UTC+05:00"
    assert subscriptions.get(100).send_time_local == time(21, 30)
