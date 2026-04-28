from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.domain.enums import LocationSource, ObservingProfile, SkyPreset, SubscriptionMode
from bot.domain.models import Location, LocationForecast, NightForecast, Subscription, User
from bot.scheduler.jobs import build_subscription_message, due_subscriptions
from bot.scheduler.runner import create_scheduler


def _subscription(
    mode: SubscriptionMode,
    threshold: int = 60,
) -> Subscription:
    return Subscription(
        user_id=100,
        enabled=True,
        mode=mode,
        send_time_local=time(9, 0),
        forecast_days=2,
        observing_profile=ObservingProfile.DEEP_SKY,
        score_threshold=threshold,
        updated_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
    )


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


def test_build_subscription_message_returns_none_for_good_conditions_without_matches() -> None:
    subscription = _subscription(SubscriptionMode.GOOD_CONDITIONS_ONLY, threshold=60)
    report = _report("Low", [20, 50])

    message = build_subscription_message(subscription, [report])

    assert message is None


def test_build_subscription_message_returns_digest_with_location_name() -> None:
    subscription = _subscription(SubscriptionMode.DAILY_DIGEST, threshold=60)
    report = _report("Dark Site", [20])

    message = build_subscription_message(subscription, [report])

    assert message is not None
    assert "Dark Site" in message


def test_build_subscription_message_for_good_conditions_includes_only_matching_nights() -> None:
    subscription = _subscription(SubscriptionMode.GOOD_CONDITIONS_ONLY, threshold=60)
    report = _report("Mixed", [20, 60, 80])

    message = build_subscription_message(subscription, [report])

    assert message is not None
    assert "2026-04-26" not in message
    assert "📅 <b>2026-04-27</b> — <b>60/100</b>" in message
    assert "📅 <b>2026-04-28</b> — <b>80/100</b>" in message


def test_create_scheduler_returns_asyncio_scheduler() -> None:
    scheduler = create_scheduler()

    assert isinstance(scheduler, AsyncIOScheduler)


def test_due_subscriptions_uses_user_timezone_and_send_time() -> None:
    subscriptions = [
        _subscription(SubscriptionMode.DAILY_DIGEST),
        Subscription(
            user_id=200,
            enabled=True,
            mode=SubscriptionMode.DAILY_DIGEST,
            send_time_local=time(10, 0),
            forecast_days=2,
            observing_profile=ObservingProfile.DEEP_SKY,
            score_threshold=60,
            updated_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
        ),
    ]
    users = {
        100: User(
            100,
            "Asia/Yekaterinburg",
            "ru",
            3,
            ObservingProfile.DEEP_SKY,
            60,
            datetime.now(tz=ZoneInfo("UTC")),
        ),
        200: User(
            200,
            "UTC",
            "ru",
            3,
            ObservingProfile.DEEP_SKY,
            60,
            datetime.now(tz=ZoneInfo("UTC")),
        ),
    }

    due = due_subscriptions(
        subscriptions,
        load_user=users.get,
        now_utc=datetime(2026, 4, 26, 4, 0, tzinfo=ZoneInfo("UTC")),
    )

    assert [subscription.user_id for subscription in due] == [100]
