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
