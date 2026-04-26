from datetime import date, datetime
from zoneinfo import ZoneInfo

from bot.domain.enums import LocationSource, SkyPreset
from bot.domain.models import Location, LocationForecast, NightForecast
from bot.services.report_formatter import format_forecast_report


def test_format_forecast_report_includes_compact_russian_night_summary() -> None:
    location = Location(
        id=1,
        user_id=10,
        name="Dark field",
        latitude=44.6,
        longitude=39.7,
        source=LocationSource.COORDINATES,
        sky_preset=SkyPreset.DARK_SITE,
        bortle_class=3,
        enabled_for_subscription=True,
        created_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
    )
    report = LocationForecast(
        location=location,
        nights=[
            NightForecast(
                night=date(2026, 4, 26),
                score=78,
                verdict="можно ехать",
                cloud_cover=15,
                high_cloud_cover=8,
                moon_phase=0.24,
                moon_visible=True,
                humidity=70,
                wind_speed=4.2,
                reasons=["мало облаков"],
            )
        ],
    )

    text = format_forecast_report([report])

    assert "Dark field" in text
    assert "78/100" in text
    assert "можно ехать" in text
    assert "Облачность: 15%" in text
