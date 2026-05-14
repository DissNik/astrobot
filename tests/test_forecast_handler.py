from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from bot.db.connection import connect
from bot.db.migrations import migrate
from bot.domain.enums import LocationSource, ObservingProfile, SkyPreset
from bot.domain.models import Location, User
from bot.handlers.forecast import forecast_callback, forecast_location_callback
from bot.providers.weather_base import DailyAstronomy, HourlyWeather, ProviderForecast
from bot.repositories.locations import LocationRepository
from bot.repositories.users import UserRepository


class FakeUser:
    def __init__(self, user_id: int) -> None:
        self.id = user_id


class FakeMessage:
    def __init__(self) -> None:
        self.answers: list[tuple[str, object | None, str | None]] = []

    async def answer(self, text: str, reply_markup=None, parse_mode: str | None = None) -> None:  # noqa: ANN001
        self.answers.append((text, reply_markup, parse_mode))


class FakeCallback:
    def __init__(self, user_id: int, data: str, message: FakeMessage | None = None) -> None:
        self.from_user = FakeUser(user_id)
        self.data = data
        self.message = message
        self.answers: list[tuple[str | None, bool | None]] = []

    async def answer(self, text: str | None = None, show_alert: bool | None = None) -> None:
        self.answers.append((text, show_alert))


class FakeWeather:
    def __init__(self) -> None:
        self.calls: list[tuple[float, float, int]] = []

    async def forecast(self, latitude: float, longitude: float, days: int) -> ProviderForecast:
        self.calls.append((latitude, longitude, days))
        return ProviderForecast(
            timezone="Europe/Moscow",
            hourly=(
                HourlyWeather(
                    time=datetime(2026, 4, 26, 22, tzinfo=ZoneInfo("Europe/Moscow")),
                    cloud_cover=10,
                    cloud_cover_low=5,
                    cloud_cover_mid=6,
                    cloud_cover_high=7,
                    humidity=55,
                    wind_speed=3.2,
                ),
            ),
            daily=(
                DailyAstronomy(
                    day=date(2026, 4, 26),
                    sunrise=datetime(2026, 4, 26, 5, tzinfo=ZoneInfo("Europe/Moscow")),
                    sunset=datetime(2026, 4, 26, 20, tzinfo=ZoneInfo("Europe/Moscow")),
                    moonrise=None,
                    moonset=None,
                    moon_phase=0.2,
                ),
                DailyAstronomy(
                    day=date(2026, 4, 27),
                    sunrise=datetime(2026, 4, 27, 5, tzinfo=ZoneInfo("Europe/Moscow")),
                    sunset=datetime(2026, 4, 27, 20, tzinfo=ZoneInfo("Europe/Moscow")),
                    moonrise=None,
                    moonset=None,
                    moon_phase=0.25,
                ),
            ),
        )


def _repositories(tmp_path: Path) -> tuple[UserRepository, LocationRepository]:
    connection = connect(tmp_path / "astrobot.sqlite3")
    migrate(connection)
    return UserRepository(connection), LocationRepository(connection)


def _save_user(users: UserRepository) -> None:
    users.upsert(
        User(
            telegram_id=100,
            timezone="UTC",
            language="en",
            forecast_days=3,
            observing_profile=ObservingProfile.DEEP_SKY,
            score_threshold=60,
            created_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
        )
    )
    users.connection.commit()


def _save_location(locations: LocationRepository) -> Location:
    location = locations.add(
        Location(
            id=None,
            user_id=100,
            name="Поле",
            latitude=45.0448,
            longitude=38.976,
            source=LocationSource.COORDINATES,
            sky_preset=SkyPreset.SUBURB,
            bortle_class=None,
            enabled_for_subscription=True,
            created_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
        )
    )
    locations.connection.commit()
    return location


@pytest.mark.asyncio
async def test_forecast_callback_shows_saved_location_buttons(tmp_path: Path) -> None:
    users, locations = _repositories(tmp_path)
    _save_user(users)
    _save_location(locations)
    message = FakeMessage()
    callback = FakeCallback(user_id=100, data="forecast:open", message=message)

    await forecast_callback(callback, locations=locations, users=users)  # type: ignore[arg-type]

    text, keyboard, parse_mode = message.answers[0]
    assert text == "<b>🔭 Choose an observing location for the forecast.</b>"
    assert keyboard.inline_keyboard[0][0].text == "Поле"
    assert keyboard.inline_keyboard[0][0].callback_data == "forecast:location:1"
    assert parse_mode == "HTML"
    assert callback.answers == [(None, None)]


@pytest.mark.asyncio
async def test_forecast_callback_prompts_to_add_location_when_list_is_empty(
    tmp_path: Path,
) -> None:
    users, locations = _repositories(tmp_path)
    message = FakeMessage()
    callback = FakeCallback(user_id=100, data="forecast:open", message=message)

    await forecast_callback(callback, locations=locations, users=users)  # type: ignore[arg-type]

    assert message.answers[0][0] == "Add an observing location in Locations first."


@pytest.mark.asyncio
async def test_forecast_location_callback_sends_report_for_selected_location(
    tmp_path: Path,
) -> None:
    users, locations = _repositories(tmp_path)
    _save_user(users)
    _save_location(locations)
    weather = FakeWeather()
    message = FakeMessage()
    callback = FakeCallback(user_id=100, data="forecast:location:1", message=message)

    await forecast_location_callback(
        callback,
        users=users,
        locations=locations,
        weather=weather,
    )  # type: ignore[arg-type]

    assert weather.calls == [(45.0448, 38.976, 4)]
    assert "Astronomical forecast" in message.answers[0][0]
    assert "Поле" in message.answers[0][0]
    assert "2026-04-26" in message.answers[0][0]
    assert message.answers[0][2] == "HTML"


@pytest.mark.asyncio
async def test_forecast_location_callback_uses_selected_russian_language(
    tmp_path: Path,
) -> None:
    users, locations = _repositories(tmp_path)
    _save_user(users)
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
    _save_location(locations)
    message = FakeMessage()
    callback = FakeCallback(user_id=100, data="forecast:location:1", message=message)

    await forecast_location_callback(
        callback,
        users=users,
        locations=locations,
        weather=FakeWeather(),
    )  # type: ignore[arg-type]

    assert "Астрономический прогноз" in message.answers[0][0]
    assert "отлично" in message.answers[0][0]
