from datetime import UTC, datetime
from pathlib import Path

import pytest

from bot.db.connection import connect
from bot.db.migrations import migrate
from bot.domain.enums import ObservingProfile
from bot.domain.models import User
from bot.handlers.locations import (
    AddLocationStates,
    add_location_coordinates_message,
    add_location_input_message,
    add_location_name_message,
    delete_location_callback,
    location_manage_callback,
    locations_add_callback,
    locations_callback,
    locations_command,
    locations_list_callback,
    rename_location_callback,
    rename_location_message,
    toggle_location_subscription_callback,
)
from bot.providers.weather_base import GeocodingCandidate
from bot.repositories.locations import LocationRepository
from bot.repositories.users import UserRepository


class FakeUser:
    def __init__(self, user_id: int) -> None:
        self.id = user_id


class FakeTelegramLocation:
    def __init__(self, latitude: float, longitude: float) -> None:
        self.latitude = latitude
        self.longitude = longitude


class FakeMessage:
    def __init__(
        self,
        user_id: int,
        text: str | None = None,
        location: FakeTelegramLocation | None = None,
    ) -> None:
        self.from_user = FakeUser(user_id)
        self.text = text
        self.location = location
        self.answers: list[str] = []
        self.edits: list[tuple[str, object | None]] = []
        self.reply_markups = []

    async def answer(self, text: str, reply_markup=None) -> None:  # noqa: ANN001
        self.answers.append(text)
        self.reply_markups.append(reply_markup)

    async def edit_text(self, text: str, reply_markup=None) -> None:  # noqa: ANN001
        self.edits.append((text, reply_markup))


class FakeCallback:
    def __init__(
        self,
        user_id: int,
        message: FakeMessage | None = None,
        data: str | None = None,
    ) -> None:
        self.from_user = FakeUser(user_id)
        self.message = message
        self.data = data
        self.answers: list[tuple[str | None, bool | None]] = []

    async def answer(self, text: str | None = None, show_alert: bool | None = None) -> None:
        self.answers.append((text, show_alert))


class FakeState:
    def __init__(self) -> None:
        self.state = None
        self.cleared = False
        self.data = {}

    async def set_state(self, state) -> None:  # noqa: ANN001
        self.state = state

    async def update_data(self, **kwargs) -> None:  # noqa: ANN003
        self.data.update(kwargs)

    async def get_data(self) -> dict:
        return self.data

    async def clear(self) -> None:
        self.cleared = True
        self.state = None
        self.data = {}


class FakeGeocoding:
    def __init__(self, candidates: list[GeocodingCandidate]) -> None:
        self.candidates = candidates
        self.queries: list[str] = []

    async def search(self, query: str, count: int = 5) -> list[GeocodingCandidate]:
        self.queries.append(query)
        return self.candidates[:count]


def _repositories(tmp_path: Path) -> tuple[UserRepository, LocationRepository]:
    connection = connect(tmp_path / "astrobot.sqlite3")
    migrate(connection)
    return UserRepository(connection), LocationRepository(connection)


@pytest.mark.asyncio
async def test_locations_add_callback_prompts_for_coordinates() -> None:
    message = FakeMessage(user_id=100)
    callback = FakeCallback(user_id=100, message=message)
    state = FakeState()

    await locations_add_callback(callback, state)  # type: ignore[arg-type]

    assert state.state == AddLocationStates.waiting_for_location_input
    assert message.answers == [
        "Send a city, coordinates like 45.0448, 38.976, or a Telegram location."
    ]
    assert callback.answers == [(None, None)]


@pytest.mark.asyncio
async def test_add_location_coordinates_message_stores_location(tmp_path: Path) -> None:
    users, locations = _repositories(tmp_path)
    message = FakeMessage(user_id=100, text="45.0448, 38.976")
    state = FakeState()

    await add_location_input_message(
        message,
        state,  # type: ignore[arg-type]
        users=users,
        locations=locations,
        connection=locations.connection,
        geocoding=FakeGeocoding([]),  # type: ignore[arg-type]
    )
    await add_location_name_message(
        FakeMessage(user_id=100, text="Поле у реки"),
        state,  # type: ignore[arg-type]
        users=users,
        locations=locations,
        connection=locations.connection,
    )

    saved_locations = locations.list_for_user(100)
    assert len(saved_locations) == 1
    assert saved_locations[0].latitude == 45.0448
    assert saved_locations[0].longitude == 38.976
    assert saved_locations[0].name == "Поле у реки"
    assert state.cleared is True
    assert message.answers == ["Enter the location name."]


@pytest.mark.asyncio
async def test_add_location_keeps_existing_user_language(tmp_path: Path) -> None:
    users, locations = _repositories(tmp_path)
    users.upsert(
        User(
            telegram_id=100,
            timezone="UTC",
            language="ru",
            forecast_days=3,
            observing_profile=ObservingProfile.DEEP_SKY,
            score_threshold=60,
            created_at=datetime.now(tz=UTC),
        )
    )
    state = FakeState()

    await add_location_input_message(
        FakeMessage(user_id=100, text="45.0448, 38.976"),
        state,  # type: ignore[arg-type]
        users=users,
        locations=locations,
        connection=locations.connection,
        geocoding=FakeGeocoding([]),  # type: ignore[arg-type]
    )
    result_message = FakeMessage(user_id=100, text="Поле")
    await add_location_name_message(
        result_message,
        state,  # type: ignore[arg-type]
        users=users,
        locations=locations,
        connection=locations.connection,
    )

    assert users.get(100).language == "ru"
    labels = [button.text for row in result_message.reply_markups[-1].keyboard for button in row]
    assert "🔭 Прогноз" in labels


@pytest.mark.asyncio
async def test_add_location_coordinates_message_rejects_invalid_input(tmp_path: Path) -> None:
    users, locations = _repositories(tmp_path)
    message = FakeMessage(user_id=100, text="нет координат")
    state = FakeState()

    await add_location_input_message(
        message,
        state,  # type: ignore[arg-type]
        users=users,
        locations=locations,
        connection=locations.connection,
        geocoding=FakeGeocoding([]),  # type: ignore[arg-type]
    )

    assert locations.list_for_user(100) == []
    assert state.cleared is False
    assert message.answers == [
        "I could not find the location. Send a city, coordinates, or a Telegram location."
    ]


@pytest.mark.asyncio
async def test_add_location_city_message_resolves_city_and_asks_for_name(tmp_path: Path) -> None:
    users, locations = _repositories(tmp_path)
    geocoding = FakeGeocoding(
        [GeocodingCandidate("Екатеринбург", "Россия", 56.8389, 60.6057, "Asia/Yekaterinburg")]
    )
    state = FakeState()

    await add_location_input_message(
        FakeMessage(user_id=100, text="Екатеринбург"),
        state,  # type: ignore[arg-type]
        users=users,
        locations=locations,
        connection=locations.connection,
        geocoding=geocoding,  # type: ignore[arg-type]
    )
    await add_location_name_message(
        FakeMessage(user_id=100, text="Дом"),
        state,  # type: ignore[arg-type]
        users=users,
        locations=locations,
        connection=locations.connection,
    )

    saved_locations = locations.list_for_user(100)
    assert geocoding.queries == ["Екатеринбург"]
    assert saved_locations[0].name == "Дом"
    assert saved_locations[0].latitude == 56.8389
    assert saved_locations[0].longitude == 60.6057
    assert saved_locations[0].source.value == "city"


@pytest.mark.asyncio
async def test_add_location_telegram_geo_stores_location_after_name(tmp_path: Path) -> None:
    users, locations = _repositories(tmp_path)
    state = FakeState()

    await add_location_input_message(
        FakeMessage(user_id=100, location=FakeTelegramLocation(55.75, 37.61)),
        state,  # type: ignore[arg-type]
        users=users,
        locations=locations,
        connection=locations.connection,
        geocoding=FakeGeocoding([]),  # type: ignore[arg-type]
    )
    await add_location_name_message(
        FakeMessage(user_id=100, text="Площадка"),
        state,  # type: ignore[arg-type]
        users=users,
        locations=locations,
        connection=locations.connection,
    )

    saved_locations = locations.list_for_user(100)
    assert saved_locations[0].source.value == "telegram_geo"
    assert saved_locations[0].name == "Площадка"


@pytest.mark.asyncio
async def test_locations_list_callback_shows_saved_locations(tmp_path: Path) -> None:
    users, locations = _repositories(tmp_path)
    state = FakeState()
    message = FakeMessage(user_id=100, text="45.0448 38.976")
    await add_location_input_message(
        message,
        state,  # type: ignore[arg-type]
        users=users,
        locations=locations,
        connection=locations.connection,
        geocoding=FakeGeocoding([]),  # type: ignore[arg-type]
    )
    await add_location_name_message(
        FakeMessage(user_id=100, text="Поле"),
        state,  # type: ignore[arg-type]
        users=users,
        locations=locations,
        connection=locations.connection,
    )
    list_message = FakeMessage(user_id=100)
    callback = FakeCallback(user_id=100, message=list_message)

    await locations_list_callback(callback, locations=locations)  # type: ignore[arg-type]

    assert list_message.answers == []
    text_value, keyboard = list_message.edits[0]
    assert text_value == "Your locations:"
    assert keyboard.inline_keyboard[0][0].text == "Поле"
    assert keyboard.inline_keyboard[0][0].callback_data == "locations:manage:1"
    assert keyboard.inline_keyboard[-1][0].text == "➕ Add location"
    assert keyboard.inline_keyboard[-1][0].callback_data == "locations:add"
    assert callback.answers == [(None, None)]


@pytest.mark.asyncio
async def test_locations_command_opens_locations_list(tmp_path: Path) -> None:
    users, locations = _repositories(tmp_path)
    message = FakeMessage(user_id=100)

    await locations_command(message, users=users, locations=locations)  # type: ignore[arg-type]

    assert message.answers[0] == "You do not have saved locations yet."
    keyboard = message.reply_markups[0]
    assert keyboard.inline_keyboard[0][0].text == "➕ Add location"
    assert keyboard.inline_keyboard[0][0].callback_data == "locations:add"


@pytest.mark.asyncio
async def test_locations_open_callback_edits_current_message(tmp_path: Path) -> None:
    users, locations = _repositories(tmp_path)
    message = FakeMessage(user_id=100)
    callback = FakeCallback(user_id=100, message=message)

    await locations_callback(callback, locations=locations, users=users)  # type: ignore[arg-type]

    assert message.answers == []
    assert message.edits[0][0] == "You do not have saved locations yet."
    assert callback.answers == [(None, None)]


@pytest.mark.asyncio
async def test_location_manage_callback_edits_current_message(tmp_path: Path) -> None:
    users, locations = _repositories(tmp_path)
    state = FakeState()
    await add_location_input_message(
        FakeMessage(user_id=100, text="45.0448 38.976"),
        state,  # type: ignore[arg-type]
        users=users,
        locations=locations,
        connection=locations.connection,
        geocoding=FakeGeocoding([]),  # type: ignore[arg-type]
    )
    await add_location_name_message(
        FakeMessage(user_id=100, text="Поле"),
        state,  # type: ignore[arg-type]
        users=users,
        locations=locations,
        connection=locations.connection,
    )
    location_id = locations.list_for_user(100)[0].id
    message = FakeMessage(user_id=100)
    callback = FakeCallback(100, message, data=f"locations:manage:{location_id}")

    await location_manage_callback(callback, locations=locations)  # type: ignore[arg-type]

    assert message.answers == []
    assert message.edits[0][0] == (
        "Поле\n"
        "Coordinates: 45.0448, 38.9760\n"
        "Source: coordinates\n"
        "Alerts: enabled"
    )


@pytest.mark.asyncio
async def test_toggle_location_subscription_edits_location_card(tmp_path: Path) -> None:
    users, locations = _repositories(tmp_path)
    state = FakeState()
    await add_location_input_message(
        FakeMessage(user_id=100, text="45.0448 38.976"),
        state,  # type: ignore[arg-type]
        users=users,
        locations=locations,
        connection=locations.connection,
        geocoding=FakeGeocoding([]),  # type: ignore[arg-type]
    )
    await add_location_name_message(
        FakeMessage(user_id=100, text="Поле"),
        state,  # type: ignore[arg-type]
        users=users,
        locations=locations,
        connection=locations.connection,
    )
    location_id = locations.list_for_user(100)[0].id
    message = FakeMessage(user_id=100)
    callback = FakeCallback(100, message, data=f"locations:toggle_subscription:{location_id}")

    await toggle_location_subscription_callback(
        callback,
        locations=locations,
        connection=locations.connection,
    )  # type: ignore[arg-type]

    assert locations.list_for_user(100)[0].enabled_for_subscription is False
    assert message.answers == []
    assert "Alerts: disabled" in message.edits[0][0]


@pytest.mark.asyncio
async def test_location_can_be_renamed(tmp_path: Path) -> None:
    users, locations = _repositories(tmp_path)
    state = FakeState()
    await add_location_input_message(
        FakeMessage(user_id=100, text="45.0448 38.976"),
        state,  # type: ignore[arg-type]
        users=users,
        locations=locations,
        connection=locations.connection,
        geocoding=FakeGeocoding([]),  # type: ignore[arg-type]
    )
    await add_location_name_message(
        FakeMessage(user_id=100, text="Старое имя"),
        state,  # type: ignore[arg-type]
        users=users,
        locations=locations,
        connection=locations.connection,
    )
    location_id = locations.list_for_user(100)[0].id
    callback = FakeCallback(100, FakeMessage(100), data=f"locations:rename:{location_id}")

    await rename_location_callback(callback, state, locations=locations)  # type: ignore[arg-type]
    await rename_location_message(
        FakeMessage(user_id=100, text="Новое имя"),
        state,  # type: ignore[arg-type]
        locations=locations,
        connection=locations.connection,
    )

    assert locations.list_for_user(100)[0].name == "Новое имя"


@pytest.mark.asyncio
async def test_location_can_be_deleted(tmp_path: Path) -> None:
    users, locations = _repositories(tmp_path)
    state = FakeState()
    await add_location_input_message(
        FakeMessage(user_id=100, text="45.0448 38.976"),
        state,  # type: ignore[arg-type]
        users=users,
        locations=locations,
        connection=locations.connection,
        geocoding=FakeGeocoding([]),  # type: ignore[arg-type]
    )
    await add_location_name_message(
        FakeMessage(user_id=100, text="Поле"),
        state,  # type: ignore[arg-type]
        users=users,
        locations=locations,
        connection=locations.connection,
    )
    location_id = locations.list_for_user(100)[0].id
    callback = FakeCallback(100, FakeMessage(100), data=f"locations:delete:{location_id}")

    await delete_location_callback(callback, locations=locations, connection=locations.connection)  # type: ignore[arg-type]

    assert locations.list_for_user(100) == []
    assert callback.message.answers == []
    text_value, keyboard = callback.message.edits[0]
    assert text_value == "You do not have saved locations yet."
    assert keyboard.inline_keyboard == [[keyboard.inline_keyboard[0][0]]]
    assert keyboard.inline_keyboard[0][0].text == "➕ Add location"
    assert keyboard.inline_keyboard[0][0].callback_data == "locations:add"


def test_location_manage_callback_exists_for_saved_location() -> None:
    assert location_manage_callback is not None


# Backward-compatible import while old tests and callers are migrated.
assert add_location_coordinates_message is add_location_input_message
