from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

from bot.db.connection import connect
from bot.db.migrations import migrate
from bot.domain.enums import LocationSource, ObservingProfile, SkyPreset, SubscriptionMode
from bot.domain.models import Location, Subscription, User
from bot.repositories.forecast_cache import ForecastCacheRepository
from bot.repositories.locations import LocationRepository
from bot.repositories.stats import StatsRepository
from bot.repositories.subscriptions import SubscriptionRepository
from bot.repositories.users import UserRepository


def create_db(tmp_path: Path):
    connection = connect(tmp_path / "test.sqlite3")
    migrate(connection)
    return connection


def sample_user(now: datetime) -> User:
    return User(100, "Europe/Moscow", "ru", 3, ObservingProfile.DEEP_SKY, 60, now)


def test_user_repository_upserts_and_fetches_user(tmp_path: Path) -> None:
    connection = create_db(tmp_path)
    repository = UserRepository(connection)
    now = datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC"))
    user = sample_user(now)

    repository.upsert(user)
    fetched = repository.get(100)

    assert fetched == user


def test_location_repository_crud(tmp_path: Path) -> None:
    connection = create_db(tmp_path)
    users = UserRepository(connection)
    locations = LocationRepository(connection)
    now = datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC"))
    users.upsert(sample_user(now))

    created = locations.add(
        Location(
            id=None,
            user_id=100,
            name="Поле",
            latitude=44.6,
            longitude=39.7,
            source=LocationSource.COORDINATES,
            sky_preset=SkyPreset.DARK_SITE,
            bortle_class=3,
            enabled_for_subscription=True,
            created_at=now,
        )
    )

    assert created.id is not None
    assert locations.list_for_user(100) == [created]

    locations.set_subscription_enabled(created.id, False)
    assert locations.list_for_user(100)[0].enabled_for_subscription is False

    locations.delete(created.id)
    assert locations.list_for_user(100) == []


def test_subscription_repository_upserts_defaults(tmp_path: Path) -> None:
    connection = create_db(tmp_path)
    users = UserRepository(connection)
    subscriptions = SubscriptionRepository(connection)
    now = datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC"))
    users.upsert(sample_user(now))

    subscription = Subscription(
        user_id=100,
        enabled=True,
        mode=SubscriptionMode.GOOD_CONDITIONS_ONLY,
        send_time_local=time(20, 30),
        forecast_days=5,
        observing_profile=ObservingProfile.PLANETARY_LUNAR,
        score_threshold=70,
        updated_at=now,
    )

    subscriptions.upsert(subscription)

    assert subscriptions.get(100) == subscription
    assert subscriptions.list_enabled() == [subscription]


def test_forecast_cache_roundtrip(tmp_path: Path) -> None:
    connection = create_db(tmp_path)
    cache = ForecastCacheRepository(connection)
    now = datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC"))

    cache.save(
        location_id=1,
        provider="open_meteo",
        forecast_date="2026-04-26",
        payload={"ok": True},
        created_at=now,
    )

    assert cache.get(location_id=1, provider="open_meteo", forecast_date="2026-04-26") == {
        "ok": True
    }


def test_stats_repository_counts(tmp_path: Path) -> None:
    connection = create_db(tmp_path)
    users = UserRepository(connection)
    locations = LocationRepository(connection)
    subscriptions = SubscriptionRepository(connection)
    stats = StatsRepository(connection)
    now = datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC"))
    users.upsert(sample_user(now))
    locations.add(
        Location(
            None,
            100,
            "Поле",
            44.6,
            39.7,
            LocationSource.CITY,
            SkyPreset.SUBURB,
            None,
            True,
            now,
        )
    )
    subscriptions.upsert(
        Subscription(
            100,
            True,
            SubscriptionMode.DAILY_DIGEST,
            time(19, 0),
            3,
            ObservingProfile.DEEP_SKY,
            60,
            now,
        )
    )

    assert stats.summary() == {
        "users": 1,
        "locations": 1,
        "active_subscriptions": 1,
    }
