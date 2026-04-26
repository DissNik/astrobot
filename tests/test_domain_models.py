from datetime import date, datetime, time
from typing import get_type_hints
from zoneinfo import ZoneInfo

import pytest

from bot.domain.enums import LocationSource, ObservingProfile, SkyPreset, SubscriptionMode
from bot.domain.models import Location, LocationForecast, NightForecast, Subscription


def test_location_uses_custom_bortle_when_present() -> None:
    location = Location(
        id=1,
        user_id=10,
        name="Dark field",
        latitude=44.6,
        longitude=39.7,
        source=LocationSource.COORDINATES,
        sky_preset=SkyPreset.CUSTOM_BORTLE,
        bortle_class=3,
        enabled_for_subscription=True,
        created_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
    )

    assert location.effective_bortle == 3


def test_location_maps_sky_preset_to_bortle_estimate() -> None:
    location = Location(
        id=1,
        user_id=10,
        name="Suburb",
        latitude=44.6,
        longitude=39.7,
        source=LocationSource.CITY,
        sky_preset=SkyPreset.SUBURB,
        bortle_class=None,
        enabled_for_subscription=False,
        created_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
    )

    assert location.effective_bortle == 6


def test_location_source_is_typed_as_location_source() -> None:
    location = Location(
        id=1,
        user_id=10,
        name="Suburb",
        latitude=44.6,
        longitude=39.7,
        source=LocationSource.CITY,
        sky_preset=SkyPreset.SUBURB,
        bortle_class=None,
        enabled_for_subscription=False,
        created_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
    )

    assert get_type_hints(Location)["source"] is LocationSource
    assert location.source is LocationSource.CITY


def test_subscription_keeps_configured_values() -> None:
    subscription = Subscription(
        user_id=10,
        enabled=False,
        mode=SubscriptionMode.DAILY_DIGEST,
        send_time_local=time(19, 0),
        forecast_days=3,
        observing_profile=ObservingProfile.DEEP_SKY,
        score_threshold=60,
        updated_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
    )

    assert subscription.forecast_days == 3
    assert subscription.score_threshold == 60


def test_night_forecast_normalizes_reasons_to_tuple() -> None:
    forecast = NightForecast(
        night=date(2026, 4, 26),
        score=78,
        verdict="можно ехать",
        cloud_cover=18,
        high_cloud_cover=10,
        moon_phase=0.24,
        moon_visible=True,
        humidity=70,
        wind_speed=4.2,
        reasons=["мало облаков"],
    )

    assert forecast.score == 78
    assert forecast.reasons == ("мало облаков",)
    with pytest.raises(AttributeError):
        forecast.reasons.append("нет ветра")


def test_location_forecast_normalizes_nights_to_tuple() -> None:
    location = Location(
        id=1,
        user_id=10,
        name="Dark field",
        latitude=44.6,
        longitude=39.7,
        source=LocationSource.COORDINATES,
        sky_preset=SkyPreset.CUSTOM_BORTLE,
        bortle_class=3,
        enabled_for_subscription=True,
        created_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
    )
    night = NightForecast(
        night=date(2026, 4, 26),
        score=78,
        verdict="можно ехать",
        cloud_cover=18,
        high_cloud_cover=10,
        moon_phase=0.24,
        moon_visible=True,
        humidity=70,
        wind_speed=4.2,
        reasons=["мало облаков"],
    )

    forecast = LocationForecast(location=location, nights=[night])

    assert forecast.nights == (night,)
    with pytest.raises(AttributeError):
        forecast.nights.append(night)
