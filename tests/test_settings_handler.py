from datetime import time
from pathlib import Path

import pytest

from bot.db.connection import connect
from bot.db.migrations import migrate
from bot.domain.enums import ObservingProfile, SubscriptionMode
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


class FakeMessage:
    def __init__(self, user_id: int, text: str | None = None) -> None:
        self.from_user = FakeUser(user_id)
        self.text = text
        self.answers: list[tuple[str, object | None]] = []

    async def answer(self, text: str, reply_markup=None) -> None:  # noqa: ANN001
        self.answers.append((text, reply_markup))


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
    assert "Profile and subscription settings." in text
    assert "3 nights" in labels
    assert "5 nights" in labels
    assert "Deep-sky" in labels
    assert "Good conditions only" in labels
    assert "English" in labels
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
    assert "Настройки профиля и рассылки." in callback.message.answers[0][0]


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
async def test_update_subscription_time_saves_subscription(tmp_path: Path) -> None:
    users, subscriptions = _repositories(tmp_path)
    state = FakeState()
    callback = FakeCallback(100, "settings:time", FakeMessage(100))

    await settings_time_callback(callback, state, users=users)  # type: ignore[arg-type]
    await settings_time_message(
        FakeMessage(100, text="21:30"),
        state,  # type: ignore[arg-type]
        users=users,
        subscriptions=subscriptions,
        connection=users.connection,
    )

    assert state.cleared is True
    assert subscriptions.get(100).send_time_local == time(21, 30)
    assert callback.message.answers == [("Enter notification time in HH:MM format.", None)]
