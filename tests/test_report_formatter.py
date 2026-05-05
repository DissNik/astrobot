from datetime import date, datetime
from zoneinfo import ZoneInfo

from bot.domain.enums import LocationSource, SkyPreset
from bot.domain.models import Location, LocationForecast, NightForecast
from bot.services.report_formatter import format_forecast_report


def test_format_forecast_report_defaults_to_english() -> None:
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

    assert text.startswith("<b>🔭 Astronomical forecast</b>\n____________\n\n")
    assert "📍 <b>Location:</b> Dark field" in text
    assert "✅ <b>2026-04-26</b> — <b>78/100</b>, good to go" in text
    assert "━━━━━━━━━━━━" not in text
    assert (
        "<blockquote>"
        "☁ <b>Clouds:</b> 15%, high 8%\n"
        "☾ <b>Moon:</b> 24%, visible\n"
        "◦ <b>Humidity:</b> 70%\n"
        "→ <b>Wind:</b> 4.2 m/s\n"
        "✓ <b>Factors:</b> low cloud cover"
        "</blockquote>"
    ) in text


def test_format_forecast_report_supports_russian() -> None:
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
                moon_visible=False,
                humidity=70,
                wind_speed=4.2,
                reasons=["мало облаков"],
            )
        ],
    )

    text = format_forecast_report([report], language="ru")

    assert text.startswith("<b>🔭 Астрономический прогноз</b>\n____________\n\n")
    assert "📍 <b>Локация:</b> Dark field" in text
    assert "✅ <b>2026-04-26</b> — <b>78/100</b>, можно ехать" in text
    assert "☁ <b>Облака:</b> 15%, высокие 8%" in text
    assert "☾ <b>Луна:</b> 24%, не видна" in text
    assert "✓ <b>Факторы:</b> мало облаков, Луна не видна" in text


def test_format_forecast_report_adds_not_visible_moon_to_english_factors() -> None:
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
                score=82,
                verdict="отлично",
                cloud_cover=10,
                high_cloud_cover=5,
                moon_phase=0.24,
                moon_visible=False,
                humidity=60,
                wind_speed=3.1,
                reasons=[],
            )
        ],
    )

    text = format_forecast_report([report])

    assert "✓ <b>Factors:</b> Moon not visible" in text


def test_format_forecast_report_uses_status_icon_for_bad_and_doubtful_nights() -> None:
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
                score=38,
                verdict="не стоит",
                cloud_cover=57,
                high_cloud_cover=0,
                moon_phase=0.43,
                moon_visible=False,
                humidity=79,
                wind_speed=10.8,
                reasons=["умеренно высокая влажность", "сильный ветер"],
            ),
            NightForecast(
                night=date(2026, 4, 27),
                score=55,
                verdict="сомнительно",
                cloud_cover=40,
                high_cloud_cover=10,
                moon_phase=0.5,
                moon_visible=True,
                humidity=65,
                wind_speed=5.1,
                reasons=[],
            ),
        ],
    )

    text = format_forecast_report([report], language="ru")

    assert "❌ <b>2026-04-26</b> — <b>38/100</b>, не стоит" in text
    assert "× <b>Факторы:</b> умеренно высокая влажность, сильный ветер, Луна не видна" in text
    assert "⚠️ <b>2026-04-27</b> — <b>55/100</b>, сомнительно" in text
    assert "! <b>Факторы:</b> нет заметных факторов" in text
    assert "</blockquote>\n\n⚠️ <b>2026-04-27</b>" in text


def test_format_forecast_report_handles_empty_reports() -> None:
    text = format_forecast_report([])

    assert text == "<b>🔭 Astronomical forecast</b>\n____________\n\nNo forecasts available."


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

    assert "No forecasts available." in text
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
