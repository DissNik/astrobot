from datetime import datetime

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
DAILY_FIELDS = ("sunrise", "sunset", "moonrise", "moonset", "moon_phase")


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

        hourly = [
            HourlyWeather(
                time=datetime.fromisoformat(timestamp),
                cloud_cover=int(hourly_payload["cloud_cover"][index]),
                cloud_cover_low=int(hourly_payload["cloud_cover_low"][index]),
                cloud_cover_mid=int(hourly_payload["cloud_cover_mid"][index]),
                cloud_cover_high=int(hourly_payload["cloud_cover_high"][index]),
                humidity=int(hourly_payload["relative_humidity_2m"][index]),
                wind_speed=float(hourly_payload["wind_speed_10m"][index]),
            )
            for index, timestamp in enumerate(hourly_payload["time"])
        ]
        daily = [
            DailyAstronomy(
                day=datetime.fromisoformat(day).date(),
                sunrise=datetime.fromisoformat(daily_payload["sunrise"][index]),
                sunset=datetime.fromisoformat(daily_payload["sunset"][index]),
                moonrise=_parse_optional_datetime(daily_payload["moonrise"][index]),
                moonset=_parse_optional_datetime(daily_payload["moonset"][index]),
                moon_phase=float(daily_payload["moon_phase"][index]),
            )
            for index, day in enumerate(daily_payload["time"])
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
