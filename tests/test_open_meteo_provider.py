from datetime import date, datetime

import httpx
import pytest
import respx

from bot.providers.geocoding import GeocodingClient
from bot.providers.open_meteo import DAILY_FIELDS, HOURLY_FIELDS, OpenMeteoClient
from bot.providers.weather_base import DailyAstronomy, HourlyWeather, ProviderForecast


def _open_meteo_payload() -> dict[str, object]:
    return {
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
    }


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
async def test_geocoding_returns_empty_list_when_results_are_missing() -> None:
    respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
        return_value=httpx.Response(200, json={}),
    )

    async with httpx.AsyncClient() as http:
        client = GeocodingClient(http)
        candidates = await client.search("No Such Place")

    assert candidates == []


def test_provider_forecast_normalizes_collections_to_tuples() -> None:
    hourly = HourlyWeather(
        time=datetime(2026, 4, 26, 20, 0),
        cloud_cover=10,
        cloud_cover_low=0,
        cloud_cover_mid=10,
        cloud_cover_high=5,
        humidity=60,
        wind_speed=3.0,
    )
    daily = DailyAstronomy(
        day=date(2026, 4, 26),
        sunrise=datetime(2026, 4, 26, 5, 30),
        sunset=datetime(2026, 4, 26, 19, 10),
        moonrise=None,
        moonset=None,
        moon_phase=0.2,
    )

    forecast = ProviderForecast(timezone="Europe/Moscow", hourly=[hourly], daily=[daily])

    assert forecast.hourly == (hourly,)
    assert forecast.daily == (daily,)
    with pytest.raises(AttributeError):
        forecast.hourly.append(hourly)


@pytest.mark.asyncio
@respx.mock
async def test_forecast_maps_open_meteo_payload() -> None:
    respx.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=httpx.Response(200, json=_open_meteo_payload())
    )

    async with httpx.AsyncClient() as http:
        client = OpenMeteoClient(http)
        forecast = await client.forecast(latitude=45.0448, longitude=38.976, days=3)

    assert forecast.timezone == "Europe/Moscow"
    assert forecast.daily[0].day == date(2026, 4, 26)
    assert forecast.hourly[0].cloud_cover == 10


@pytest.mark.asyncio
@respx.mock
async def test_forecast_request_includes_expected_params() -> None:
    route = respx.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=httpx.Response(200, json=_open_meteo_payload())
    )

    async with httpx.AsyncClient() as http:
        client = OpenMeteoClient(http)
        await client.forecast(latitude=45.0448, longitude=38.976, days=3)

    params = route.calls.last.request.url.params
    assert params["latitude"] == "45.0448"
    assert params["longitude"] == "38.976"
    assert params["forecast_days"] == "3"
    assert params["timezone"] == "auto"
    assert set(params["hourly"].split(",")) >= set(HOURLY_FIELDS)
    assert set(params["daily"].split(",")) >= set(DAILY_FIELDS)


@pytest.mark.asyncio
@respx.mock
async def test_forecast_treats_missing_moon_arrays_as_none() -> None:
    payload = _open_meteo_payload()
    daily_payload = payload["daily"]
    assert isinstance(daily_payload, dict)
    daily_payload.pop("moonrise")
    daily_payload.pop("moonset")
    respx.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=httpx.Response(200, json=payload)
    )

    async with httpx.AsyncClient() as http:
        client = OpenMeteoClient(http)
        forecast = await client.forecast(latitude=45.0448, longitude=38.976, days=3)

    assert forecast.daily[0].moonrise is None
    assert forecast.daily[0].moonset is None


@pytest.mark.asyncio
@respx.mock
async def test_forecast_treats_explicit_moon_nulls_as_none() -> None:
    payload = _open_meteo_payload()
    daily_payload = payload["daily"]
    assert isinstance(daily_payload, dict)
    daily_payload["moonrise"] = [None]
    daily_payload["moonset"] = [None]
    respx.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=httpx.Response(200, json=payload)
    )

    async with httpx.AsyncClient() as http:
        client = OpenMeteoClient(http)
        forecast = await client.forecast(latitude=45.0448, longitude=38.976, days=3)

    assert forecast.daily[0].moonrise is None
    assert forecast.daily[0].moonset is None


@pytest.mark.asyncio
@respx.mock
async def test_forecast_raises_clear_error_for_required_array_length_mismatch() -> None:
    payload = _open_meteo_payload()
    hourly_payload = payload["hourly"]
    assert isinstance(hourly_payload, dict)
    hourly_payload["cloud_cover"] = [10]
    respx.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=httpx.Response(200, json=payload)
    )

    async with httpx.AsyncClient() as http:
        client = OpenMeteoClient(http)
        with pytest.raises(ValueError, match="hourly.cloud_cover length mismatch"):
            await client.forecast(latitude=45.0448, longitude=38.976, days=3)
