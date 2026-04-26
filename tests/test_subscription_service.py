from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from bot.domain.enums import LocationSource, SkyPreset, SubscriptionMode
from bot.domain.models import Location, LocationForecast, NightForecast
from bot.services.subscription_service import select_reports_for_subscription


def _location(name: str) -> Location:
    return Location(
        id=1,
        user_id=100,
        name=name,
        latitude=45.0,
        longitude=39.0,
        source=LocationSource.COORDINATES,
        sky_preset=SkyPreset.DARK_SITE,
        bortle_class=3,
        enabled_for_subscription=True,
        created_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
    )


def _night(score: int, day: int) -> NightForecast:
    return NightForecast(
        night=date(2026, 4, day),
        score=score,
        verdict="можно ехать",
        cloud_cover=20,
        high_cloud_cover=10,
        moon_phase=0.2,
        moon_visible=False,
        humidity=60,
        wind_speed=3.0,
        reasons=["мало облаков"],
    )


def _report(name: str, scores: list[int]) -> LocationForecast:
    return LocationForecast(
        location=_location(name),
        nights=[_night(score, day) for day, score in enumerate(scores, start=26)],
    )


def test_daily_digest_always_returns_reports() -> None:
    low = _report("Low", [10, 20])
    empty = _report("Empty", [])

    selected = select_reports_for_subscription(
        reports=[low, empty],
        mode=SubscriptionMode.DAILY_DIGEST,
        threshold=60,
    )

    assert selected == [low, empty]


def test_good_conditions_only_filters_below_threshold() -> None:
    low = _report("Low", [10, 59])
    high = _report("High", [60])

    selected = select_reports_for_subscription(
        reports=[low, high],
        mode=SubscriptionMode.GOOD_CONDITIONS_ONLY,
        threshold=60,
    )

    assert selected == [high]


def test_good_conditions_only_keeps_reports_with_any_night_at_or_above_threshold() -> None:
    first = _report("First", [10, 70])
    second = _report("Second", [65, 20])
    third = _report("Third", [20, 30])

    selected = select_reports_for_subscription(
        reports=[first, second, third],
        mode=SubscriptionMode.GOOD_CONDITIONS_ONLY,
        threshold=65,
    )

    assert [report.location.name for report in selected] == ["First", "Second"]
    assert [night.score for night in selected[0].nights] == [70]
    assert [night.score for night in selected[1].nights] == [65]


def test_select_reports_for_subscription_normalizes_raw_mode() -> None:
    low = _report("Low", [10])

    selected = select_reports_for_subscription(
        reports=[low],
        mode="daily_digest",
        threshold=60,
    )

    assert selected == [low]


def test_select_reports_for_subscription_rejects_invalid_mode() -> None:
    with pytest.raises(ValueError, match="mode must be a valid SubscriptionMode"):
        select_reports_for_subscription(reports=[], mode="invalid", threshold=60)


@pytest.mark.parametrize("threshold", [-1, 101])
def test_select_reports_for_subscription_rejects_invalid_threshold(threshold: int) -> None:
    with pytest.raises(ValueError, match="threshold must be between 0 and 100"):
        select_reports_for_subscription(
            reports=[],
            mode=SubscriptionMode.DAILY_DIGEST,
            threshold=threshold,
        )
