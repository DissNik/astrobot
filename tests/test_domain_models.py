from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from bot.domain.enums import ObservingProfile, SkyPreset, SubscriptionMode
from bot.domain.models import Location, NightForecast, Subscription


def test_location_uses_custom_bortle_when_present() -> None:
    location = Location(
        id=1,
        user_id=10,
        name="Dark field",
        latitude=44.6,
        longitude=39.7,
        source="coordinates",
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
        source="city",
        sky_preset=SkyPreset.SUBURB,
        bortle_class=None,
        enabled_for_subscription=False,
        created_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
    )

    assert location.effective_bortle == 6


def test_subscription_defaults_match_spec() -> None:
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


def test_night_forecast_best_score_property() -> None:
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
