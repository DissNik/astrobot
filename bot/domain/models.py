from dataclasses import dataclass
from datetime import date, datetime, time

from bot.domain.enums import LocationSource, ObservingProfile, SkyPreset, SubscriptionMode


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
    source: LocationSource
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
    last_sent_on: date | None = None


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
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "reasons", tuple(self.reasons))


@dataclass(frozen=True)
class LocationForecast:
    location: Location
    nights: tuple[NightForecast, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "nights", tuple(self.nights))
