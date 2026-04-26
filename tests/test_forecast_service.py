from datetime import date, datetime
from zoneinfo import ZoneInfo

from bot.domain.enums import LocationSource, ObservingProfile, SkyPreset
from bot.domain.models import Location
from bot.providers.weather_base import DailyAstronomy, HourlyWeather, ProviderForecast
from bot.services.forecast_service import build_location_forecast, provider_days_for_nights


def test_build_location_forecast_aggregates_hourly_weather_in_useful_night_window() -> None:
    location = Location(
        id=1,
        user_id=10,
        name="Dark field",
        latitude=44.6,
        longitude=39.7,
        source=LocationSource.COORDINATES,
        sky_preset=SkyPreset.DARK_SITE,
        bortle_class=3,
        enabled_for_subscription=True,
        created_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
    )
    provider_forecast = ProviderForecast(
        timezone="Europe/Moscow",
        hourly=[
            HourlyWeather(
                time=datetime(2026, 4, 26, 19, 30),
                cloud_cover=90,
                cloud_cover_low=80,
                cloud_cover_mid=70,
                cloud_cover_high=60,
                humidity=80,
                wind_speed=9.0,
            ),
            HourlyWeather(
                time=datetime(2026, 4, 26, 20, 0),
                cloud_cover=10,
                cloud_cover_low=0,
                cloud_cover_mid=5,
                cloud_cover_high=5,
                humidity=60,
                wind_speed=3.0,
            ),
            HourlyWeather(
                time=datetime(2026, 4, 27, 0, 0),
                cloud_cover=20,
                cloud_cover_low=10,
                cloud_cover_mid=15,
                cloud_cover_high=10,
                humidity=70,
                wind_speed=4.0,
            ),
            HourlyWeather(
                time=datetime(2026, 4, 27, 5, 30),
                cloud_cover=90,
                cloud_cover_low=80,
                cloud_cover_mid=70,
                cloud_cover_high=60,
                humidity=80,
                wind_speed=9.0,
            ),
        ],
        daily=[
            DailyAstronomy(
                day=date(2026, 4, 26),
                sunrise=datetime(2026, 4, 26, 5, 30),
                sunset=datetime(2026, 4, 26, 19, 0),
                moonrise=datetime(2026, 4, 26, 10, 0),
                moonset=datetime(2026, 4, 27, 2, 0),
                moon_phase=0.2,
            ),
            DailyAstronomy(
                day=date(2026, 4, 27),
                sunrise=datetime(2026, 4, 27, 6, 0),
                sunset=datetime(2026, 4, 27, 19, 2),
                moonrise=datetime(2026, 4, 27, 11, 0),
                moonset=datetime(2026, 4, 28, 2, 40),
                moon_phase=0.25,
            ),
        ],
    )

    result = build_location_forecast(location, provider_forecast, ObservingProfile.DEEP_SKY)

    assert result.location is location
    assert len(result.nights) == 1
    assert result.nights[0].night == date(2026, 4, 26)
    assert result.nights[0].cloud_cover == 15


def test_build_location_forecast_marks_moon_visible_when_moonrise_is_inside_window() -> None:
    location = Location(
        id=1,
        user_id=10,
        name="Dark field",
        latitude=44.6,
        longitude=39.7,
        source=LocationSource.COORDINATES,
        sky_preset=SkyPreset.DARK_SITE,
        bortle_class=3,
        enabled_for_subscription=True,
        created_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
    )
    provider_forecast = ProviderForecast(
        timezone="Europe/Moscow",
        hourly=[
            HourlyWeather(
                time=datetime(2026, 4, 26, 23, 30),
                cloud_cover=10,
                cloud_cover_low=0,
                cloud_cover_mid=5,
                cloud_cover_high=5,
                humidity=60,
                wind_speed=3.0,
            ),
        ],
        daily=[
            DailyAstronomy(
                day=date(2026, 4, 26),
                sunrise=datetime(2026, 4, 26, 5, 30),
                sunset=datetime(2026, 4, 26, 19, 0),
                moonrise=datetime(2026, 4, 26, 23, 0),
                moonset=datetime(2026, 4, 26, 9, 0),
                moon_phase=0.2,
            ),
            DailyAstronomy(
                day=date(2026, 4, 27),
                sunrise=datetime(2026, 4, 27, 6, 0),
                sunset=datetime(2026, 4, 27, 19, 2),
                moonrise=None,
                moonset=None,
                moon_phase=0.25,
            ),
        ],
    )

    result = build_location_forecast(location, provider_forecast, ObservingProfile.DEEP_SKY)

    assert result.nights[0].moon_visible is True


def test_build_location_forecast_checks_next_daily_record_for_after_midnight_moonrise() -> None:
    location = Location(
        id=1,
        user_id=10,
        name="Dark field",
        latitude=44.6,
        longitude=39.7,
        source=LocationSource.COORDINATES,
        sky_preset=SkyPreset.DARK_SITE,
        bortle_class=3,
        enabled_for_subscription=True,
        created_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
    )
    provider_forecast = ProviderForecast(
        timezone="Europe/Moscow",
        hourly=[
            HourlyWeather(
                time=datetime(2026, 4, 27, 2, 30),
                cloud_cover=10,
                cloud_cover_low=0,
                cloud_cover_mid=5,
                cloud_cover_high=5,
                humidity=60,
                wind_speed=3.0,
            ),
        ],
        daily=[
            DailyAstronomy(
                day=date(2026, 4, 26),
                sunrise=datetime(2026, 4, 26, 5, 30),
                sunset=datetime(2026, 4, 26, 19, 0),
                moonrise=None,
                moonset=None,
                moon_phase=0.2,
            ),
            DailyAstronomy(
                day=date(2026, 4, 27),
                sunrise=datetime(2026, 4, 27, 6, 0),
                sunset=datetime(2026, 4, 27, 19, 2),
                moonrise=datetime(2026, 4, 27, 2, 0),
                moonset=None,
                moon_phase=0.25,
            ),
        ],
    )

    result = build_location_forecast(location, provider_forecast, ObservingProfile.DEEP_SKY)

    assert result.nights[0].moon_visible is True


def test_provider_days_for_nights_requests_one_extra_daily_record() -> None:
    assert provider_days_for_nights(3) == 4
