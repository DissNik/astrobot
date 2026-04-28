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

    assert text.startswith("🔭 <b>Астрономический прогноз</b>")
    assert "📍 <b>Локация:</b> Dark field" in text
    assert "📅 <b>2026-04-26</b> — <b>78/100</b>, можно ехать" in text
    assert "☁️ <b>Облачность:</b> 15% (высокая: 8%)" in text
    assert "🌙 <b>Луна:</b> 24%, видна" in text
    assert "💧 <b>Влажность:</b> 70%" in text
    assert "💨 <b>Ветер:</b> 4.2 м/с" in text
    assert "📝 <b>Причины:</b> мало облаков" in text


def test_format_forecast_report_handles_empty_reports() -> None:
    text = format_forecast_report([])

    assert "Астрономический прогноз" in text
    assert "Нет доступных прогнозов." in text


def test_format_forecast_report_skips_locations_without_nights() -> None:
    location = Location(
        id=1,
        user_id=10,
        name="Empty field",
        latitude=44.6,
        longitude=39.7,
        source=LocationSource.COORDINATES,
        sky_preset=SkyPreset.DARK_SITE,
        bortle_class=3,
        enabled_for_subscription=True,
        created_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
    )

    text = format_forecast_report([LocationForecast(location=location, nights=[])])

    assert "Нет доступных прогнозов." in text
    assert "Empty field" not in text


def test_format_forecast_report_escapes_location_name() -> None:
    location = Location(
        id=1,
        user_id=10,
        name="<test & field>",
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

    assert "&lt;test &amp; field&gt;" in text
    assert "<test & field>" not in text
