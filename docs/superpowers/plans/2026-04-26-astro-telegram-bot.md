# Astro Telegram Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python Telegram bot that forecasts astronomy trip conditions for saved observation locations and sends configurable daily subscription messages.

**Architecture:** Use a modular monolith: aiogram handlers, services, repositories, Open-Meteo providers, scoring, formatting, and scheduler live in one Python package. Telegram handlers call services; services own workflows; repositories hide SQLite; providers hide external APIs.

**Tech Stack:** Python 3.12, aiogram 3, httpx, pydantic-settings, APScheduler, SQLite, pytest, pytest-asyncio, respx, ruff.

---

## File Structure Map

- `pyproject.toml`: package metadata, dependencies, pytest and ruff config.
- `requirements.txt`: pinned or compatible runtime and test dependencies for venv deployment.
- `.env.example`: documented environment variables.
- `README.md`: setup, run, test, and systemd deployment instructions.
- `bot/__init__.py`: package marker.
- `bot/main.py`: application entrypoint, dependency wiring, polling startup.
- `bot/config.py`: environment parsing and settings model.
- `bot/domain/enums.py`: shared enums for profiles, subscription modes, location source, sky quality.
- `bot/domain/models.py`: dataclasses for users, locations, subscriptions, forecasts, reports.
- `bot/db/connection.py`: SQLite connection factory and row helpers.
- `bot/db/migrations.py`: idempotent schema creation.
- `bot/repositories/*.py`: SQLite repositories for users, locations, subscriptions, forecast cache, stats.
- `bot/providers/weather_base.py`: provider protocol and provider-facing typed results.
- `bot/providers/geocoding.py`: Open-Meteo geocoding client.
- `bot/providers/open_meteo.py`: Open-Meteo forecast client and response mapping.
- `bot/services/location_service.py`: add/list/update/delete location workflows.
- `bot/services/scoring_service.py`: astronomy condition scoring.
- `bot/services/forecast_service.py`: nightly aggregation and report construction.
- `bot/services/report_formatter.py`: Russian text rendering.
- `bot/services/subscription_service.py`: subscription settings and send decision logic.
- `bot/texts/ru.py`: Russian UI strings.
- `bot/keyboards/*.py`: inline keyboard factories.
- `bot/handlers/*.py`: aiogram handlers for user flows.
- `bot/scheduler/runner.py`: APScheduler lifecycle.
- `bot/scheduler/jobs.py`: subscription job execution.
- `tests/`: unit and integration tests using mocked network and temporary SQLite.
- `scripts/run_migrations.py`: CLI for schema creation.

---

### Task 1: Project Skeleton And Configuration

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `README.md`
- Create: `bot/__init__.py`
- Create: `bot/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing configuration tests**

Create `tests/test_config.py`:

```python
from pathlib import Path

import pytest
from pydantic import ValidationError

from bot.config import Settings


def test_settings_load_required_values(tmp_path: Path) -> None:
    settings = Settings(
        telegram_bot_token="123:abc",
        owner_telegram_id=42,
        database_path=tmp_path / "astrobot.sqlite3",
        log_level="DEBUG",
    )

    assert settings.telegram_bot_token == "123:abc"
    assert settings.owner_telegram_id == 42
    assert settings.database_path == tmp_path / "astrobot.sqlite3"
    assert settings.log_level == "DEBUG"


def test_settings_default_values(tmp_path: Path) -> None:
    settings = Settings(
        telegram_bot_token="123:abc",
        owner_telegram_id=42,
        database_path=tmp_path / "astrobot.sqlite3",
    )

    assert settings.log_level == "INFO"


def test_settings_rejects_empty_token(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        Settings(
            telegram_bot_token="",
            owner_telegram_id=42,
            database_path=tmp_path / "astrobot.sqlite3",
        )
```

- [ ] **Step 2: Run the failing tests**

Run: `pytest tests/test_config.py -v`

Expected: import failure because `bot.config` does not exist.

- [ ] **Step 3: Add project metadata and dependencies**

Create `pyproject.toml`:

```toml
[project]
name = "astrobot"
version = "0.1.0"
description = "Telegram bot for astronomy trip forecasts"
requires-python = ">=3.12"
dependencies = [
  "aiogram>=3.6,<4",
  "apscheduler>=3.10,<4",
  "httpx>=0.27,<1",
  "pydantic>=2.7,<3",
  "pydantic-settings>=2.2,<3",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2,<9",
  "pytest-asyncio>=0.23,<1",
  "respx>=0.21,<1",
  "ruff>=0.4,<1",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

Create `requirements.txt`:

```text
aiogram>=3.6,<4
apscheduler>=3.10,<4
httpx>=0.27,<1
pydantic>=2.7,<3
pydantic-settings>=2.2,<3
pytest>=8.2,<9
pytest-asyncio>=0.23,<1
respx>=0.21,<1
ruff>=0.4,<1
```

Create `.env.example`:

```env
TELEGRAM_BOT_TOKEN=123456:replace-me
OWNER_TELEGRAM_ID=123456789
DATABASE_PATH=./data/astrobot.sqlite3
LOG_LEVEL=INFO
```

Create `README.md`:

```markdown
# Astrobot

Telegram bot for astronomy trip forecasts.

## Local Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`, then run migrations:

```bash
.venv/bin/python scripts/run_migrations.py
```

Run the bot:

```bash
.venv/bin/python -m bot.main
```

Run tests:

```bash
.venv/bin/pytest
```

## systemd

```ini
[Unit]
Description=Astrobot Telegram Bot
After=network.target

[Service]
WorkingDirectory=/opt/astrobot
EnvironmentFile=/opt/astrobot/.env
ExecStart=/opt/astrobot/.venv/bin/python -m bot.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
```

- [ ] **Step 4: Add settings implementation**

Create `bot/__init__.py`:

```python
"""Astrobot package."""
```

Create `bot/config.py`:

```python
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    owner_telegram_id: int = Field(alias="OWNER_TELEGRAM_ID")
    database_path: Path = Field(alias="DATABASE_PATH")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @field_validator("telegram_bot_token")
    @classmethod
    def token_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("TELEGRAM_BOT_TOKEN must not be empty")
        return value

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        normalized = value.upper()
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if normalized not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(sorted(allowed))}")
        return normalized
```

- [ ] **Step 5: Run tests and lint**

Run: `pytest tests/test_config.py -v`

Expected: all tests pass.

Run: `ruff check .`

Expected: no lint errors.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml requirements.txt .env.example README.md bot/__init__.py bot/config.py tests/test_config.py
git commit -m "chore: scaffold python project"
```

---

### Task 2: Domain Models And Enums

**Files:**
- Create: `bot/domain/__init__.py`
- Create: `bot/domain/enums.py`
- Create: `bot/domain/models.py`
- Create: `tests/test_domain_models.py`

- [ ] **Step 1: Write failing domain tests**

Create `tests/test_domain_models.py`:

```python
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
```

- [ ] **Step 2: Run failing tests**

Run: `pytest tests/test_domain_models.py -v`

Expected: import failure because `bot.domain` does not exist.

- [ ] **Step 3: Add enums**

Create `bot/domain/__init__.py`:

```python
"""Domain models and enums."""
```

Create `bot/domain/enums.py`:

```python
from enum import StrEnum


class ObservingProfile(StrEnum):
    DEEP_SKY = "deep_sky"
    PLANETARY_LUNAR = "planetary_lunar"


class SubscriptionMode(StrEnum):
    DAILY_DIGEST = "daily_digest"
    GOOD_CONDITIONS_ONLY = "good_conditions_only"


class LocationSource(StrEnum):
    CITY = "city"
    COORDINATES = "coordinates"
    TELEGRAM_GEO = "telegram_geo"


class SkyPreset(StrEnum):
    CITY = "city"
    SUBURB = "suburb"
    DARK_SITE = "dark_site"
    CUSTOM_BORTLE = "custom_bortle"
```

- [ ] **Step 4: Add domain models**

Create `bot/domain/models.py`:

```python
from dataclasses import dataclass
from datetime import date, datetime, time

from bot.domain.enums import ObservingProfile, SkyPreset, SubscriptionMode


@dataclass(frozen=True)
class User:
    telegram_id: int
    timezone: str
    language: str
    forecast_days: int
    observing_profile: ObservingProfile
    score_threshold: int
    created_at: datetime


@dataclass(frozen=True)
class Location:
    id: int | None
    user_id: int
    name: str
    latitude: float
    longitude: float
    source: str
    sky_preset: SkyPreset
    bortle_class: int | None
    enabled_for_subscription: bool
    created_at: datetime

    @property
    def effective_bortle(self) -> int:
        if self.bortle_class is not None:
            return self.bortle_class

        return {
            SkyPreset.CITY: 8,
            SkyPreset.SUBURB: 6,
            SkyPreset.DARK_SITE: 3,
            SkyPreset.CUSTOM_BORTLE: 5,
        }[self.sky_preset]


@dataclass(frozen=True)
class Subscription:
    user_id: int
    enabled: bool
    mode: SubscriptionMode
    send_time_local: time
    forecast_days: int
    observing_profile: ObservingProfile
    score_threshold: int
    updated_at: datetime


@dataclass(frozen=True)
class NightForecast:
    night: date
    score: int
    verdict: str
    cloud_cover: int
    high_cloud_cover: int
    moon_phase: float
    moon_visible: bool
    humidity: int
    wind_speed: float
    reasons: list[str]


@dataclass(frozen=True)
class LocationForecast:
    location: Location
    nights: list[NightForecast]
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_domain_models.py -v`

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add bot/domain tests/test_domain_models.py
git commit -m "feat: add domain models"
```

---

### Task 3: SQLite Schema And Repositories

**Files:**
- Create: `bot/db/__init__.py`
- Create: `bot/db/connection.py`
- Create: `bot/db/migrations.py`
- Create: `bot/repositories/__init__.py`
- Create: `bot/repositories/users.py`
- Create: `bot/repositories/locations.py`
- Create: `bot/repositories/subscriptions.py`
- Create: `bot/repositories/forecast_cache.py`
- Create: `bot/repositories/stats.py`
- Create: `scripts/run_migrations.py`
- Create: `tests/test_repositories.py`

- [ ] **Step 1: Write failing repository tests**

Create `tests/test_repositories.py` with tests for migration, user upsert, locations, subscriptions, cache, and stats:

```python
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

from bot.db.connection import connect
from bot.db.migrations import migrate
from bot.domain.enums import ObservingProfile, SkyPreset, SubscriptionMode
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


def test_user_repository_upserts_and_fetches_user(tmp_path: Path) -> None:
    connection = create_db(tmp_path)
    repository = UserRepository(connection)
    now = datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC"))

    user = User(
        telegram_id=100,
        timezone="Asia/Yekaterinburg",
        language="ru",
        forecast_days=3,
        observing_profile=ObservingProfile.DEEP_SKY,
        score_threshold=60,
        created_at=now,
    )

    repository.upsert(user)
    fetched = repository.get(100)

    assert fetched == user


def test_location_repository_crud(tmp_path: Path) -> None:
    connection = create_db(tmp_path)
    users = UserRepository(connection)
    locations = LocationRepository(connection)
    now = datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC"))
    users.upsert(User(100, "Europe/Moscow", "ru", 3, ObservingProfile.DEEP_SKY, 60, now))

    created = locations.add(
        Location(
            id=None,
            user_id=100,
            name="Поле",
            latitude=44.6,
            longitude=39.7,
            source="coordinates",
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
    users.upsert(User(100, "Europe/Moscow", "ru", 3, ObservingProfile.DEEP_SKY, 60, now))

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

    cache.save(location_id=1, provider="open_meteo", forecast_date="2026-04-26", payload={"ok": True}, created_at=now)

    assert cache.get(location_id=1, provider="open_meteo", forecast_date="2026-04-26") == {"ok": True}


def test_stats_repository_counts(tmp_path: Path) -> None:
    connection = create_db(tmp_path)
    users = UserRepository(connection)
    locations = LocationRepository(connection)
    subscriptions = SubscriptionRepository(connection)
    stats = StatsRepository(connection)
    now = datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC"))
    users.upsert(User(100, "Europe/Moscow", "ru", 3, ObservingProfile.DEEP_SKY, 60, now))
    locations.add(Location(None, 100, "Поле", 44.6, 39.7, "city", SkyPreset.SUBURB, None, True, now))
    subscriptions.upsert(Subscription(100, True, SubscriptionMode.DAILY_DIGEST, time(19, 0), 3, ObservingProfile.DEEP_SKY, 60, now))

    assert stats.summary() == {
        "users": 1,
        "locations": 1,
        "active_subscriptions": 1,
    }
```

- [ ] **Step 2: Run failing tests**

Run: `pytest tests/test_repositories.py -v`

Expected: import failure because database and repository modules do not exist.

- [ ] **Step 3: Implement SQLite connection and migrations**

Create `bot/db/__init__.py`:

```python
"""Database helpers."""
```

Create `bot/db/connection.py`:

```python
import sqlite3
from pathlib import Path


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection
```

Create `bot/db/migrations.py` with `CREATE TABLE IF NOT EXISTS` statements for `users`, `locations`, `subscriptions`, and `forecast_cache`. Store datetimes as ISO strings, booleans as integers, and enum values as strings. Add indexes on `locations.user_id`, `subscriptions.enabled`, and `forecast_cache(location_id, provider, forecast_date)`.

Create `scripts/run_migrations.py`:

```python
from bot.config import Settings
from bot.db.connection import connect
from bot.db.migrations import migrate


def main() -> None:
    settings = Settings()
    connection = connect(settings.database_path)
    migrate(connection)
    connection.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Implement repositories**

Create repository classes with the exact public methods used by the tests:

```python
class UserRepository:
    def __init__(self, connection): ...
    def upsert(self, user): ...
    def get(self, telegram_id): ...

class LocationRepository:
    def __init__(self, connection): ...
    def add(self, location): ...
    def list_for_user(self, user_id): ...
    def set_subscription_enabled(self, location_id, enabled): ...
    def delete(self, location_id): ...

class SubscriptionRepository:
    def __init__(self, connection): ...
    def upsert(self, subscription): ...
    def get(self, user_id): ...
    def list_enabled(self): ...

class ForecastCacheRepository:
    def __init__(self, connection): ...
    def save(self, location_id, provider, forecast_date, payload, created_at): ...
    def get(self, location_id, provider, forecast_date): ...

class StatsRepository:
    def __init__(self, connection): ...
    def summary(self): ...
```

Use mapper helpers inside each repository file so SQL row conversion is local to the repository.

- [ ] **Step 5: Run repository tests**

Run: `pytest tests/test_repositories.py -v`

Expected: all tests pass.

- [ ] **Step 6: Run full current test suite and lint**

Run: `pytest -v`

Expected: all current tests pass.

Run: `ruff check .`

Expected: no lint errors.

- [ ] **Step 7: Commit**

```bash
git add bot/db bot/repositories scripts/run_migrations.py tests/test_repositories.py
git commit -m "feat: add sqlite repositories"
```

---

### Task 4: Scoring Service

**Files:**
- Create: `bot/services/__init__.py`
- Create: `bot/services/scoring_service.py`
- Create: `tests/test_scoring_service.py`

- [ ] **Step 1: Write failing scoring tests**

Create `tests/test_scoring_service.py`:

```python
from bot.domain.enums import ObservingProfile, SkyPreset
from bot.services.scoring_service import ScoreInput, score_conditions


def test_clear_dark_deep_sky_night_scores_high() -> None:
    result = score_conditions(
        ScoreInput(
            profile=ObservingProfile.DEEP_SKY,
            cloud_cover=10,
            high_cloud_cover=5,
            moon_phase=0.1,
            moon_visible=False,
            humidity=55,
            fog_risk=0,
            wind_speed=3,
            sky_preset=SkyPreset.DARK_SITE,
            bortle_class=3,
        )
    )

    assert result.score >= 85
    assert result.verdict == "отлично"


def test_cloudy_night_scores_low() -> None:
    result = score_conditions(
        ScoreInput(
            profile=ObservingProfile.DEEP_SKY,
            cloud_cover=85,
            high_cloud_cover=70,
            moon_phase=0.2,
            moon_visible=False,
            humidity=60,
            fog_risk=0,
            wind_speed=4,
            sky_preset=SkyPreset.DARK_SITE,
            bortle_class=3,
        )
    )

    assert result.score <= 35
    assert result.verdict == "не стоит"
    assert any("облачность" in reason for reason in result.reasons)


def test_full_moon_penalizes_deep_sky_more_than_planetary() -> None:
    common = dict(
        cloud_cover=15,
        high_cloud_cover=5,
        moon_phase=0.98,
        moon_visible=True,
        humidity=55,
        fog_risk=0,
        wind_speed=3,
        sky_preset=SkyPreset.DARK_SITE,
        bortle_class=3,
    )

    deep_sky = score_conditions(ScoreInput(profile=ObservingProfile.DEEP_SKY, **common))
    planetary = score_conditions(ScoreInput(profile=ObservingProfile.PLANETARY_LUNAR, **common))

    assert planetary.score > deep_sky.score


def test_city_sky_penalizes_deep_sky() -> None:
    dark = score_conditions(
        ScoreInput(
            profile=ObservingProfile.DEEP_SKY,
            cloud_cover=15,
            high_cloud_cover=5,
            moon_phase=0.1,
            moon_visible=False,
            humidity=55,
            fog_risk=0,
            wind_speed=3,
            sky_preset=SkyPreset.DARK_SITE,
            bortle_class=3,
        )
    )
    city = score_conditions(
        ScoreInput(
            profile=ObservingProfile.DEEP_SKY,
            cloud_cover=15,
            high_cloud_cover=5,
            moon_phase=0.1,
            moon_visible=False,
            humidity=55,
            fog_risk=0,
            wind_speed=3,
            sky_preset=SkyPreset.CITY,
            bortle_class=8,
        )
    )

    assert city.score < dark.score
```

- [ ] **Step 2: Run failing tests**

Run: `pytest tests/test_scoring_service.py -v`

Expected: import failure because `bot.services.scoring_service` does not exist.

- [ ] **Step 3: Implement scoring**

Create `bot/services/__init__.py`:

```python
"""Application services."""
```

Create `bot/services/scoring_service.py` with:

```python
from dataclasses import dataclass

from bot.domain.enums import ObservingProfile, SkyPreset


@dataclass(frozen=True)
class ScoreInput:
    profile: ObservingProfile
    cloud_cover: int
    high_cloud_cover: int
    moon_phase: float
    moon_visible: bool
    humidity: int
    fog_risk: int
    wind_speed: float
    sky_preset: SkyPreset
    bortle_class: int | None


@dataclass(frozen=True)
class ScoreResult:
    score: int
    verdict: str
    reasons: list[str]


def score_conditions(data: ScoreInput) -> ScoreResult:
    score = 100
    reasons: list[str] = []

    cloud_penalty = round(data.cloud_cover * 0.45)
    score -= cloud_penalty
    if data.cloud_cover >= 60:
        reasons.append("высокая общая облачность")
    elif data.cloud_cover <= 20:
        reasons.append("мало облаков")

    high_cloud_penalty = round(data.high_cloud_cover * 0.15)
    score -= high_cloud_penalty
    if data.high_cloud_cover >= 45:
        reasons.append("много высокой облачности")

    if data.profile is ObservingProfile.DEEP_SKY:
        moon_penalty = round(data.moon_phase * 20)
        if data.moon_visible:
            moon_penalty += 10
        score -= moon_penalty
        if moon_penalty >= 15:
            reasons.append("Луна мешает deep-sky")

        bortle = data.bortle_class or _preset_bortle(data.sky_preset)
        sky_penalty = max(0, bortle - 3) * 4
        score -= sky_penalty
        if bortle >= 7:
            reasons.append("светлое небо")
    else:
        if data.moon_visible:
            reasons.append("Луна не критична для планет")

    if data.humidity >= 85:
        score -= 10
        reasons.append("высокая влажность")
    elif data.humidity >= 75:
        score -= 5
        reasons.append("умеренно высокая влажность")

    if data.fog_risk >= 60:
        score -= 12
        reasons.append("риск тумана")

    if data.wind_speed >= 10:
        score -= 10
        reasons.append("сильный ветер")
    elif data.wind_speed >= 6:
        score -= 5
        reasons.append("умеренный ветер")

    score = max(0, min(100, score))
    return ScoreResult(score=score, verdict=_verdict(score), reasons=reasons)


def _preset_bortle(preset: SkyPreset) -> int:
    return {
        SkyPreset.CITY: 8,
        SkyPreset.SUBURB: 6,
        SkyPreset.DARK_SITE: 3,
        SkyPreset.CUSTOM_BORTLE: 5,
    }[preset]


def _verdict(score: int) -> str:
    if score >= 80:
        return "отлично"
    if score >= 60:
        return "можно ехать"
    if score >= 40:
        return "сомнительно"
    return "не стоит"
```

- [ ] **Step 4: Run scoring tests**

Run: `pytest tests/test_scoring_service.py -v`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add bot/services tests/test_scoring_service.py
git commit -m "feat: add astronomy scoring"
```

---

### Task 5: Open-Meteo Provider And Geocoding

**Files:**
- Create: `bot/providers/__init__.py`
- Create: `bot/providers/weather_base.py`
- Create: `bot/providers/geocoding.py`
- Create: `bot/providers/open_meteo.py`
- Create: `tests/test_open_meteo_provider.py`

- [ ] **Step 1: Write mocked provider tests**

Create `tests/test_open_meteo_provider.py`:

```python
from datetime import date

import httpx
import pytest
import respx

from bot.providers.geocoding import GeocodingClient
from bot.providers.open_meteo import OpenMeteoClient


@pytest.mark.asyncio
@respx.mock
async def test_geocoding_returns_candidates() -> None:
    respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Краснодар",
                        "country": "Россия",
                        "latitude": 45.0448,
                        "longitude": 38.976,
                        "timezone": "Europe/Moscow",
                    }
                ]
            },
        )
    )

    async with httpx.AsyncClient() as http:
        client = GeocodingClient(http)
        candidates = await client.search("Краснодар")

    assert candidates[0].name == "Краснодар"
    assert candidates[0].latitude == 45.0448
    assert candidates[0].timezone == "Europe/Moscow"


@pytest.mark.asyncio
@respx.mock
async def test_forecast_maps_open_meteo_payload() -> None:
    respx.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=httpx.Response(
            200,
            json={
                "timezone": "Europe/Moscow",
                "hourly": {
                    "time": ["2026-04-26T20:00", "2026-04-26T21:00"],
                    "cloud_cover": [10, 20],
                    "cloud_cover_low": [0, 5],
                    "cloud_cover_mid": [10, 15],
                    "cloud_cover_high": [5, 8],
                    "relative_humidity_2m": [60, 65],
                    "wind_speed_10m": [3.0, 4.0],
                },
                "daily": {
                    "time": ["2026-04-26"],
                    "sunrise": ["2026-04-26T05:30"],
                    "sunset": ["2026-04-26T19:10"],
                    "moonrise": ["2026-04-26T10:00"],
                    "moonset": ["2026-04-27T02:00"],
                    "moon_phase": [0.2],
                },
            },
        )
    )

    async with httpx.AsyncClient() as http:
        client = OpenMeteoClient(http)
        forecast = await client.forecast(latitude=45.0448, longitude=38.976, days=3)

    assert forecast.timezone == "Europe/Moscow"
    assert forecast.daily[0].day == date(2026, 4, 26)
    assert forecast.hourly[0].cloud_cover == 10
```

- [ ] **Step 2: Run failing tests**

Run: `pytest tests/test_open_meteo_provider.py -v`

Expected: import failure because provider modules do not exist.

- [ ] **Step 3: Add provider models and clients**

Create `bot/providers/__init__.py`:

```python
"""Weather and geocoding providers."""
```

Create `bot/providers/weather_base.py` with dataclasses:

```python
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class GeocodingCandidate:
    name: str
    country: str
    latitude: float
    longitude: float
    timezone: str


@dataclass(frozen=True)
class HourlyWeather:
    time: datetime
    cloud_cover: int
    cloud_cover_low: int
    cloud_cover_mid: int
    cloud_cover_high: int
    humidity: int
    wind_speed: float


@dataclass(frozen=True)
class DailyAstronomy:
    day: date
    sunrise: datetime
    sunset: datetime
    moonrise: datetime | None
    moonset: datetime | None
    moon_phase: float


@dataclass(frozen=True)
class ProviderForecast:
    timezone: str
    hourly: list[HourlyWeather]
    daily: list[DailyAstronomy]
```

Create `bot/providers/geocoding.py`:

```python
import httpx

from bot.providers.weather_base import GeocodingCandidate


class GeocodingClient:
    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def search(self, query: str, count: int = 5) -> list[GeocodingCandidate]:
        response = await self._http.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": query, "count": count, "language": "ru", "format": "json"},
        )
        response.raise_for_status()
        payload = response.json()
        return [
            GeocodingCandidate(
                name=item["name"],
                country=item.get("country", ""),
                latitude=float(item["latitude"]),
                longitude=float(item["longitude"]),
                timezone=item.get("timezone", "UTC"),
            )
            for item in payload.get("results", [])
        ]
```

Create `bot/providers/open_meteo.py` with `OpenMeteoClient.forecast()`. Request `hourly` fields from the spec, `daily` astronomy fields, `timezone=auto`, and `forecast_days=days`. Parse ISO timestamps with `datetime.fromisoformat`.

- [ ] **Step 4: Run provider tests**

Run: `pytest tests/test_open_meteo_provider.py -v`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add bot/providers tests/test_open_meteo_provider.py
git commit -m "feat: add open meteo provider"
```

---

### Task 6: Forecast Aggregation And Report Formatting

**Files:**
- Create: `bot/services/forecast_service.py`
- Create: `bot/services/report_formatter.py`
- Create: `bot/texts/__init__.py`
- Create: `bot/texts/ru.py`
- Create: `tests/test_forecast_service.py`
- Create: `tests/test_report_formatter.py`

- [ ] **Step 1: Write forecast aggregation tests**

Create `tests/test_forecast_service.py`:

```python
from datetime import date, datetime
from zoneinfo import ZoneInfo

from bot.domain.enums import ObservingProfile, SkyPreset
from bot.domain.models import Location
from bot.providers.weather_base import DailyAstronomy, HourlyWeather, ProviderForecast
from bot.services.forecast_service import build_location_forecast


def test_build_location_forecast_aggregates_night_window() -> None:
    tz = ZoneInfo("Europe/Moscow")
    location = Location(None, 100, "Поле", 45.0, 39.0, "coordinates", SkyPreset.DARK_SITE, 3, True, datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")))
    provider_forecast = ProviderForecast(
        timezone="Europe/Moscow",
        hourly=[
            HourlyWeather(datetime(2026, 4, 26, 19, 0, tzinfo=tz), 90, 80, 80, 80, 80, 3),
            HourlyWeather(datetime(2026, 4, 26, 20, 30, tzinfo=tz), 10, 0, 5, 5, 55, 3),
            HourlyWeather(datetime(2026, 4, 27, 3, 30, tzinfo=tz), 20, 0, 5, 10, 60, 4),
            HourlyWeather(datetime(2026, 4, 27, 5, 30, tzinfo=tz), 95, 90, 90, 90, 80, 3),
        ],
        daily=[
            DailyAstronomy(
                day=date(2026, 4, 26),
                sunrise=datetime(2026, 4, 26, 5, 30, tzinfo=tz),
                sunset=datetime(2026, 4, 26, 19, 10, tzinfo=tz),
                moonrise=datetime(2026, 4, 26, 10, 0, tzinfo=tz),
                moonset=datetime(2026, 4, 27, 2, 0, tzinfo=tz),
                moon_phase=0.2,
            ),
            DailyAstronomy(
                day=date(2026, 4, 27),
                sunrise=datetime(2026, 4, 27, 5, 20, tzinfo=tz),
                sunset=datetime(2026, 4, 27, 19, 20, tzinfo=tz),
                moonrise=None,
                moonset=None,
                moon_phase=0.25,
            ),
        ],
    )

    result = build_location_forecast(location, provider_forecast, ObservingProfile.DEEP_SKY)

    assert result.location == location
    assert len(result.nights) == 1
    assert result.nights[0].night == date(2026, 4, 26)
    assert result.nights[0].cloud_cover == 15
```

- [ ] **Step 2: Write report formatter tests**

Create `tests/test_report_formatter.py`:

```python
from datetime import date, datetime
from zoneinfo import ZoneInfo

from bot.domain.enums import SkyPreset
from bot.domain.models import Location, LocationForecast, NightForecast
from bot.services.report_formatter import format_forecast_report


def test_format_forecast_report_in_russian() -> None:
    location = Location(1, 100, "Поле", 45.0, 39.0, "coordinates", SkyPreset.DARK_SITE, 3, True, datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")))
    report = LocationForecast(
        location=location,
        nights=[
            NightForecast(date(2026, 4, 26), 78, "можно ехать", 15, 5, 0.2, True, 60, 3.5, ["мало облаков"]),
        ],
    )

    text = format_forecast_report([report])

    assert "Поле" in text
    assert "78/100" in text
    assert "можно ехать" in text
    assert "Облачность: 15%" in text
```

- [ ] **Step 3: Run failing tests**

Run: `pytest tests/test_forecast_service.py tests/test_report_formatter.py -v`

Expected: import failures for forecast and formatter services.

- [ ] **Step 4: Implement forecast aggregation**

Create `bot/services/forecast_service.py` with:

- `build_location_forecast(location, provider_forecast, profile) -> LocationForecast`;
- night window from `sunset + 1 hour` to next day's `sunrise - 1 hour`;
- averages rounded to integers for cloud, high cloud, humidity;
- average wind speed rounded to one decimal;
- `moon_visible=True` when moonrise/moonset overlaps the night window or moonset occurs inside it;
- call `score_conditions()`.

- [ ] **Step 5: Implement Russian formatter**

Create `bot/texts/__init__.py`:

```python
"""Localized text templates."""
```

Create `bot/texts/ru.py`:

```python
FORECAST_TITLE = "Астропрогноз"
```

Create `bot/services/report_formatter.py` with `format_forecast_report(reports: list[LocationForecast]) -> str`. Include location name, night date, score, verdict, cloud cover, Moon percentage, humidity, wind, and reasons.

- [ ] **Step 6: Run tests**

Run: `pytest tests/test_forecast_service.py tests/test_report_formatter.py -v`

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add bot/services/forecast_service.py bot/services/report_formatter.py bot/texts tests/test_forecast_service.py tests/test_report_formatter.py
git commit -m "feat: build forecast reports"
```

---

### Task 7: Location And Subscription Services

**Files:**
- Create: `bot/services/location_service.py`
- Create: `bot/services/subscription_service.py`
- Create: `tests/test_location_service.py`
- Create: `tests/test_subscription_service.py`

- [ ] **Step 1: Write location service tests**

Create `tests/test_location_service.py`:

```python
from datetime import datetime
from zoneinfo import ZoneInfo

from bot.domain.enums import SkyPreset
from bot.services.location_service import build_location_from_coordinates


def test_build_location_from_coordinates_validates_bortle() -> None:
    created_at = datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC"))

    location = build_location_from_coordinates(
        user_id=100,
        name="Поле",
        latitude=45.0,
        longitude=39.0,
        sky_preset=SkyPreset.CUSTOM_BORTLE,
        bortle_class=4,
        enabled_for_subscription=True,
        created_at=created_at,
    )

    assert location.name == "Поле"
    assert location.bortle_class == 4
```

- [ ] **Step 2: Write subscription service tests**

Create `tests/test_subscription_service.py`:

```python
from datetime import date, datetime
from zoneinfo import ZoneInfo

from bot.domain.enums import SkyPreset, SubscriptionMode
from bot.domain.models import Location, LocationForecast, NightForecast
from bot.services.subscription_service import select_reports_for_subscription


def make_report(score: int) -> LocationForecast:
    location = Location(1, 100, "Поле", 45.0, 39.0, "coordinates", SkyPreset.DARK_SITE, 3, True, datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")))
    return LocationForecast(
        location=location,
        nights=[NightForecast(date(2026, 4, 26), score, "можно ехать", 10, 5, 0.2, False, 55, 3.0, ["мало облаков"])],
    )


def test_daily_digest_always_returns_reports() -> None:
    reports = select_reports_for_subscription([make_report(30)], SubscriptionMode.DAILY_DIGEST, threshold=60)

    assert len(reports) == 1


def test_good_conditions_only_filters_below_threshold() -> None:
    reports = select_reports_for_subscription([make_report(59)], SubscriptionMode.GOOD_CONDITIONS_ONLY, threshold=60)

    assert reports == []


def test_good_conditions_only_keeps_matching_reports() -> None:
    reports = select_reports_for_subscription([make_report(75)], SubscriptionMode.GOOD_CONDITIONS_ONLY, threshold=60)

    assert len(reports) == 1
```

- [ ] **Step 3: Run failing tests**

Run: `pytest tests/test_location_service.py tests/test_subscription_service.py -v`

Expected: import failures for new services.

- [ ] **Step 4: Implement services**

Create `bot/services/location_service.py` with `build_location_from_coordinates()` and validation:

- latitude must be from `-90` to `90`;
- longitude must be from `-180` to `180`;
- `bortle_class` must be `1..9` when provided;
- if `sky_preset` is `CUSTOM_BORTLE`, `bortle_class` is required.

Create `bot/services/subscription_service.py` with `select_reports_for_subscription()`. For `DAILY_DIGEST`, return all reports. For `GOOD_CONDITIONS_ONLY`, return reports where at least one night score is greater than or equal to threshold.

- [ ] **Step 5: Run service tests**

Run: `pytest tests/test_location_service.py tests/test_subscription_service.py -v`

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add bot/services/location_service.py bot/services/subscription_service.py tests/test_location_service.py tests/test_subscription_service.py
git commit -m "feat: add location and subscription services"
```

---

### Task 8: Telegram Keyboards And Handlers

**Files:**
- Create: `bot/keyboards/__init__.py`
- Create: `bot/keyboards/menu.py`
- Create: `bot/keyboards/locations.py`
- Create: `bot/keyboards/subscription.py`
- Create: `bot/handlers/__init__.py`
- Create: `bot/handlers/start.py`
- Create: `bot/handlers/menu.py`
- Create: `bot/handlers/locations.py`
- Create: `bot/handlers/forecast.py`
- Create: `bot/handlers/subscription.py`
- Create: `bot/handlers/settings.py`
- Create: `bot/handlers/admin.py`
- Create: `tests/test_keyboards.py`
- Create: `tests/test_admin_handler.py`

- [ ] **Step 1: Write keyboard tests**

Create `tests/test_keyboards.py`:

```python
from bot.keyboards.menu import main_menu_keyboard


def test_main_menu_keyboard_contains_core_actions() -> None:
    keyboard = main_menu_keyboard()
    labels = [button.text for row in keyboard.inline_keyboard for button in row]

    assert "Прогноз" in labels
    assert "Точки" in labels
    assert "Рассылка" in labels
    assert "Настройки" in labels
```

- [ ] **Step 2: Write admin access test**

Create `tests/test_admin_handler.py`:

```python
from bot.handlers.admin import is_owner


def test_is_owner_allows_configured_owner() -> None:
    assert is_owner(user_id=42, owner_id=42) is True


def test_is_owner_rejects_other_users() -> None:
    assert is_owner(user_id=100, owner_id=42) is False
```

- [ ] **Step 3: Run failing tests**

Run: `pytest tests/test_keyboards.py tests/test_admin_handler.py -v`

Expected: import failures for keyboard and handler modules.

- [ ] **Step 4: Implement keyboards**

Create keyboard factories returning `InlineKeyboardMarkup`:

- `main_menu_keyboard()`;
- `locations_keyboard()`;
- `subscription_keyboard()`;
- small callback data strings such as `forecast:open`, `locations:open`, `subscription:open`.

- [ ] **Step 5: Implement handlers with dependency injection stubs**

Create handler modules that expose `router = Router()` where needed. Implement:

- `/start` sends Russian greeting and main menu;
- `/locations`, `/forecast`, `/subscribe`, `/settings` entrypoints send menu text;
- text/geolocation capture functions are present but call service methods through injected dependencies from `bot.main`;
- `/stats` uses `is_owner()` and stats repository summary.

Keep business decisions in services, not handlers.

- [ ] **Step 6: Run tests**

Run: `pytest tests/test_keyboards.py tests/test_admin_handler.py -v`

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add bot/keyboards bot/handlers tests/test_keyboards.py tests/test_admin_handler.py
git commit -m "feat: add telegram menus"
```

---

### Task 9: Scheduler And Subscription Job

**Files:**
- Create: `bot/scheduler/__init__.py`
- Create: `bot/scheduler/jobs.py`
- Create: `bot/scheduler/runner.py`
- Create: `tests/test_scheduler_jobs.py`

- [ ] **Step 1: Write scheduler job tests**

Create `tests/test_scheduler_jobs.py`:

```python
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from bot.domain.enums import ObservingProfile, SkyPreset, SubscriptionMode
from bot.domain.models import Location, LocationForecast, NightForecast, Subscription
from bot.scheduler.jobs import build_subscription_message


@pytest.mark.asyncio
async def test_build_subscription_message_returns_none_when_no_good_conditions() -> None:
    subscription = Subscription(100, True, SubscriptionMode.GOOD_CONDITIONS_ONLY, datetime.now().time(), 3, ObservingProfile.DEEP_SKY, 80, datetime.now(tz=ZoneInfo("UTC")))
    location = Location(1, 100, "Поле", 45.0, 39.0, "coordinates", SkyPreset.DARK_SITE, 3, True, datetime.now(tz=ZoneInfo("UTC")))
    report = LocationForecast(location, [NightForecast(date(2026, 4, 26), 60, "можно ехать", 10, 5, 0.2, False, 55, 3.0, ["мало облаков"])])

    message = build_subscription_message(subscription, [report])

    assert message is None


@pytest.mark.asyncio
async def test_build_subscription_message_returns_digest() -> None:
    subscription = Subscription(100, True, SubscriptionMode.DAILY_DIGEST, datetime.now().time(), 3, ObservingProfile.DEEP_SKY, 60, datetime.now(tz=ZoneInfo("UTC")))
    location = Location(1, 100, "Поле", 45.0, 39.0, "coordinates", SkyPreset.DARK_SITE, 3, True, datetime.now(tz=ZoneInfo("UTC")))
    report = LocationForecast(location, [NightForecast(date(2026, 4, 26), 60, "можно ехать", 10, 5, 0.2, False, 55, 3.0, ["мало облаков"])])

    message = build_subscription_message(subscription, [report])

    assert message is not None
    assert "Поле" in message
```

- [ ] **Step 2: Run failing tests**

Run: `pytest tests/test_scheduler_jobs.py -v`

Expected: import failure because scheduler modules do not exist.

- [ ] **Step 3: Implement scheduler job helpers**

Create `bot/scheduler/__init__.py`:

```python
"""Subscription scheduler."""
```

Create `bot/scheduler/jobs.py` with:

- `build_subscription_message(subscription, reports) -> str | None`;
- `send_due_subscriptions(...)` orchestration function that loads enabled subscriptions, gathers enabled locations, calls forecast provider/service, filters via subscription service, sends messages, and logs failures.

Create `bot/scheduler/runner.py` with:

- `create_scheduler() -> AsyncIOScheduler`;
- `schedule_subscription_job(scheduler, job_func)`.

Use one frequent scheduler tick, for example every minute, and let job logic decide which users are due by local time. This avoids creating one APScheduler job per user in MVP.

- [ ] **Step 4: Run scheduler tests**

Run: `pytest tests/test_scheduler_jobs.py -v`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add bot/scheduler tests/test_scheduler_jobs.py
git commit -m "feat: add subscription scheduler"
```

---

### Task 10: Application Entrypoint And Smoke Test

**Files:**
- Create: `bot/main.py`
- Create: `tests/test_app_smoke.py`
- Modify: `README.md`

- [ ] **Step 1: Write smoke test**

Create `tests/test_app_smoke.py`:

```python
from pathlib import Path

from bot.config import Settings
from bot.main import create_app_context


def test_create_app_context_initializes_dependencies(tmp_path: Path) -> None:
    settings = Settings(
        telegram_bot_token="123:abc",
        owner_telegram_id=42,
        database_path=tmp_path / "astrobot.sqlite3",
    )

    context = create_app_context(settings)

    assert context.bot is not None
    assert context.dispatcher is not None
    assert context.connection is not None
```

- [ ] **Step 2: Run failing smoke test**

Run: `pytest tests/test_app_smoke.py -v`

Expected: import failure because `bot.main` does not exist.

- [ ] **Step 3: Implement app context and entrypoint**

Create `bot/main.py` with:

- `AppContext` dataclass containing settings, bot, dispatcher, connection, repositories, providers, scheduler;
- `create_app_context(settings: Settings) -> AppContext`;
- register handlers;
- run migrations during startup;
- create `httpx.AsyncClient`;
- start scheduler;
- start aiogram polling;
- close HTTP and database resources on shutdown.

Do not start polling inside `create_app_context`; keep it testable.

- [ ] **Step 4: Update README run instructions**

Extend `README.md` with:

```markdown
## Run

```bash
.venv/bin/python -m bot.main
```

The MVP uses Telegram polling, so no public domain or HTTPS endpoint is required.
```

- [ ] **Step 5: Run smoke test**

Run: `pytest tests/test_app_smoke.py -v`

Expected: test passes without contacting Telegram.

- [ ] **Step 6: Run full verification**

Run: `pytest -v`

Expected: all tests pass.

Run: `ruff check .`

Expected: no lint errors.

- [ ] **Step 7: Commit**

```bash
git add bot/main.py tests/test_app_smoke.py README.md
git commit -m "feat: wire bot application"
```

---

### Task 11: End-To-End Manual Verification Prep

**Files:**
- Modify: `README.md`
- Create: `docs/manual-test-checklist.md`

- [ ] **Step 1: Add manual checklist**

Create `docs/manual-test-checklist.md`:

```markdown
# Manual Test Checklist

- [ ] `/start` shows the main menu.
- [ ] `/locations` opens location management.
- [ ] Adding a city location resolves at least one geocoding candidate.
- [ ] Adding coordinates stores the expected latitude and longitude.
- [ ] Adding Telegram geolocation stores the expected coordinates.
- [ ] Location can be renamed.
- [ ] Location can be enabled and disabled for subscription.
- [ ] `/forecast` returns a 3-night forecast by default.
- [ ] Forecast horizon can be changed to 5 and 7 nights.
- [ ] Observing profile can be changed between deep-sky and planetary/lunar.
- [ ] Subscription can be enabled and disabled.
- [ ] Daily digest mode sends a message at the configured local time.
- [ ] Good-conditions-only mode sends only when a score reaches the threshold.
- [ ] `/stats` works for `OWNER_TELEGRAM_ID`.
- [ ] `/stats` is rejected for non-owner users.
- [ ] Bot continues running if Open-Meteo returns an error.
```

- [ ] **Step 2: Add README verification section**

Add:

```markdown
## Manual Verification

Use `docs/manual-test-checklist.md` before deploying to a long-running VPS service.
```

- [ ] **Step 3: Run docs check**

Run: `ruff check .`

Expected: no lint errors.

- [ ] **Step 4: Commit**

```bash
git add README.md docs/manual-test-checklist.md
git commit -m "docs: add manual verification checklist"
```

---

## Self-Review Notes

- Spec coverage: the plan covers Python setup, SQLite repositories, Open-Meteo provider, scoring, multiple locations, subscriptions, Russian formatting, owner stats, systemd deployment docs, and tests.
- Scope: meteoblue, Windy, webhook deployment, PostgreSQL, broadcast, and full i18n are intentionally excluded from implementation tasks.
- Test strategy: network calls are mocked; SQLite tests use temporary databases; smoke test does not start Telegram polling.
- Type consistency: enums use `deep_sky`, `planetary_lunar`, `daily_digest`, and `good_conditions_only` consistently in Python identifiers and storage values.
