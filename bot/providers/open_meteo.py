from datetime import date, datetime

import httpx

from bot.providers.weather_base import DailyAstronomy, HourlyWeather, ProviderForecast

HOURLY_FIELDS = (
    "cloud_cover",
    "cloud_cover_low",
    "cloud_cover_mid",
    "cloud_cover_high",
    "relative_humidity_2m",
    "wind_speed_10m",
)
DAILY_FIELDS = ("sunrise", "sunset")
SYNODIC_MONTH_DAYS = 29.53058867
KNOWN_NEW_MOON = date(2000, 1, 6)


class OpenMeteoClient:
    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def forecast(self, latitude: float, longitude: float, days: int) -> ProviderForecast:
        response = await self._http.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "hourly": ",".join(HOURLY_FIELDS),
                "daily": ",".join(DAILY_FIELDS),
                "timezone": "auto",
                "forecast_days": days,
            },
        )
        response.raise_for_status()
        payload = response.json()

        hourly_payload = payload["hourly"]
        daily_payload = payload["daily"]

        hourly_time = hourly_payload["time"]
        hourly_count = len(hourly_time)
        cloud_cover = _required_array(hourly_payload, "cloud_cover", hourly_count, "hourly")
        cloud_cover_low = _required_array(hourly_payload, "cloud_cover_low", hourly_count, "hourly")
        cloud_cover_mid = _required_array(hourly_payload, "cloud_cover_mid", hourly_count, "hourly")
        cloud_cover_high = _required_array(
            hourly_payload, "cloud_cover_high", hourly_count, "hourly"
        )
        humidity = _required_array(hourly_payload, "relative_humidity_2m", hourly_count, "hourly")
        wind_speed = _required_array(hourly_payload, "wind_speed_10m", hourly_count, "hourly")
        hourly = [
            HourlyWeather(
                time=datetime.fromisoformat(timestamp),
                cloud_cover=int(cloud_cover[index]),
                cloud_cover_low=int(cloud_cover_low[index]),
                cloud_cover_mid=int(cloud_cover_mid[index]),
                cloud_cover_high=int(cloud_cover_high[index]),
                humidity=int(humidity[index]),
                wind_speed=float(wind_speed[index]),
            )
            for index, timestamp in enumerate(hourly_time)
        ]

        daily_time = daily_payload["time"]
        daily_count = len(daily_time)
        sunrise = _required_array(daily_payload, "sunrise", daily_count, "daily")
        sunset = _required_array(daily_payload, "sunset", daily_count, "daily")
        moonrise = _optional_array(daily_payload, "moonrise", daily_count, "daily")
        moonset = _optional_array(daily_payload, "moonset", daily_count, "daily")
        moon_phase = _optional_array(daily_payload, "moon_phase", daily_count, "daily")
        daily = [
            DailyAstronomy(
                day=datetime.fromisoformat(day).date(),
                sunrise=datetime.fromisoformat(sunrise[index]),
                sunset=datetime.fromisoformat(sunset[index]),
                moonrise=_parse_optional_datetime(moonrise[index]),
                moonset=_parse_optional_datetime(moonset[index]),
                moon_phase=_parse_moon_phase(moon_phase[index], datetime.fromisoformat(day).date()),
            )
            for index, day in enumerate(daily_time)
        ]

        return ProviderForecast(
            timezone=payload.get("timezone", "UTC"),
            hourly=hourly,
            daily=daily,
        )


def _parse_optional_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


def _parse_moon_phase(value: str | int | float | None, day: date) -> float:
    if value is not None:
        return float(value)
    return _approximate_moon_phase(day)


def _approximate_moon_phase(day: date) -> float:
    days_since_known_new_moon = (day - KNOWN_NEW_MOON).days
    return (days_since_known_new_moon % SYNODIC_MONTH_DAYS) / SYNODIC_MONTH_DAYS


def _required_array(
    payload: dict[str, list[str | int | float | None]],
    field: str,
    expected_length: int,
    section: str,
) -> list[str | int | float | None]:
    values = payload[field]
    if len(values) != expected_length:
        raise ValueError(
            f"{section}.{field} length mismatch: expected {expected_length}, got {len(values)}"
        )
    return values


def _optional_array(
    payload: dict[str, list[str | int | float | None]],
    field: str,
    expected_length: int,
    section: str,
) -> list[str | int | float | None] | tuple[None, ...]:
    values = payload.get(field)
    if values is None:
        return (None,) * expected_length
    if len(values) != expected_length:
        raise ValueError(
            f"{section}.{field} length mismatch: expected {expected_length}, got {len(values)}"
        )
    return values
