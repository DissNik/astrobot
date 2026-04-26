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
    hourly: tuple[HourlyWeather, ...]
    daily: tuple[DailyAstronomy, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "hourly", tuple(self.hourly))
        object.__setattr__(self, "daily", tuple(self.daily))
