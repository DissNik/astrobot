from collections.abc import Iterable
from datetime import datetime, timedelta
from statistics import mean

from bot.domain.enums import ObservingProfile
from bot.domain.models import Location, LocationForecast, NightForecast
from bot.providers.weather_base import DailyAstronomy, HourlyWeather, ProviderForecast
from bot.services.scoring_service import ScoreInput, score_conditions


def build_location_forecast(
    location: Location,
    provider_forecast: ProviderForecast,
    profile: ObservingProfile,
) -> LocationForecast:
    """Build nightly forecasts.

    Provider data must include one extra daily astronomy record because each
    night uses the current sunset and the next day's sunrise.
    """
    daily_by_date = {day.day: day for day in provider_forecast.daily}
    nights: list[NightForecast] = []

    for astronomy in provider_forecast.daily:
        next_astronomy = daily_by_date.get(astronomy.day + timedelta(days=1))
        if next_astronomy is None:
            continue

        window_start = astronomy.sunset + timedelta(hours=1)
        window_end = next_astronomy.sunrise - timedelta(hours=1)
        hourly = _hourly_in_window(provider_forecast.hourly, window_start, window_end)
        if not hourly:
            continue

        cloud_cover = _rounded_average(sample.cloud_cover for sample in hourly)
        high_cloud_cover = _rounded_average(sample.cloud_cover_high for sample in hourly)
        humidity = _rounded_average(sample.humidity for sample in hourly)
        wind_speed = round(mean(sample.wind_speed for sample in hourly), 1)
        moon_visible = _moon_visible(astronomy, next_astronomy, window_start, window_end)

        score = score_conditions(
            ScoreInput(
                profile=profile,
                cloud_cover=cloud_cover,
                high_cloud_cover=high_cloud_cover,
                moon_phase=astronomy.moon_phase,
                moon_visible=moon_visible,
                humidity=humidity,
                fog_risk=0,
                wind_speed=wind_speed,
                sky_preset=location.sky_preset,
                bortle_class=location.bortle_class,
            )
        )
        nights.append(
            NightForecast(
                night=astronomy.day,
                score=score.score,
                verdict=score.verdict,
                cloud_cover=cloud_cover,
                high_cloud_cover=high_cloud_cover,
                moon_phase=astronomy.moon_phase,
                moon_visible=moon_visible,
                humidity=humidity,
                wind_speed=wind_speed,
                reasons=score.reasons,
            )
        )

    return LocationForecast(location=location, nights=tuple(nights))


def provider_days_for_nights(nights: int) -> int:
    if nights < 1:
        raise ValueError("nights must be greater than or equal to 1")
    return nights + 1


def _hourly_in_window(
    hourly: tuple[HourlyWeather, ...],
    window_start: datetime,
    window_end: datetime,
) -> list[HourlyWeather]:
    return [sample for sample in hourly if window_start <= sample.time <= window_end]


def _rounded_average(values: Iterable[int]) -> int:
    return round(mean(values))


def _moon_visible(
    astronomy: DailyAstronomy,
    next_astronomy: DailyAstronomy,
    window_start: datetime,
    window_end: datetime,
) -> bool:
    for moon_event in (
        astronomy.moonrise,
        astronomy.moonset,
        next_astronomy.moonrise,
        next_astronomy.moonset,
    ):
        if moon_event is not None and window_start <= moon_event <= window_end:
            return True

    for moonrise, moonset in (
        (astronomy.moonrise, astronomy.moonset),
        (next_astronomy.moonrise, next_astronomy.moonset),
    ):
        if (
            moonrise is not None
            and moonset is not None
            and moonrise <= window_end
            and moonset >= window_start
        ):
            return True

    return False
