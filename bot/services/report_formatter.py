from html import escape

from bot.domain.models import LocationForecast, NightForecast
from bot.texts.i18n import text, translate_reason, translate_verdict
from bot.texts.message_format import format_menu_message

FORECAST_PARSE_MODE = "HTML"
MOON_NOT_VISIBLE_FACTOR = "Луна не видна"


def format_forecast_report(reports: list[LocationForecast], language: str = "en") -> str:
    title = text("forecast_title", language)
    lines: list[str] = []
    reports_with_nights = [report for report in reports if report.nights]

    if not reports_with_nights:
        return format_menu_message("🔭", title, text("no_forecasts", language))

    for report in reports_with_nights:
        lines.append("")
        lines.append(f"📍 <b>{text('location', language)}:</b> {escape(report.location.name)}")

        for night in report.nights:
            moon_percent = round(night.moon_phase * 100)
            moon_visibility = (
                text("visible", language) if night.moon_visible else text("not_visible", language)
            )
            details = "\n".join(
                [
                    (
                        f"☁ <b>{text('clouds', language)}:</b> {night.cloud_cover}%, "
                        f"{text('high_cloud_cover', language)} {night.high_cloud_cover}%"
                    ),
                    f"☾ <b>{text('moon', language)}:</b> {moon_percent}%, {moon_visibility}",
                    f"◦ <b>{text('humidity', language)}:</b> {night.humidity}%",
                    f"→ <b>{text('wind', language)}:</b> {night.wind_speed:.1f} m/s",
                    (
                        f"<b>{text('factors', language)}:</b> "
                        f"{_format_display_factors(night, language)}"
                    ),
                ]
            )
            lines.extend(
                [
                    "",
                    (
                        f"{_verdict_icon(night.verdict)} <b>{night.night:%Y-%m-%d}</b> — "
                        f"<b>{night.score}/100</b>, "
                        f"{escape(translate_verdict(night.verdict, language))}"
                    ),
                    f"<blockquote>{details}</blockquote>",
                ]
            )

    return format_menu_message("🔭", title, "\n".join(lines), escape_body=False)


def _verdict_icon(verdict: str) -> str:
    if verdict == "не стоит":
        return "❌"
    if verdict == "сомнительно":
        return "⚠️"
    return "✅"


def _format_display_factors(night: NightForecast, language: str) -> str:
    factors = list(night.reasons)
    if not night.moon_visible:
        factors.append(MOON_NOT_VISIBLE_FACTOR)

    if not factors:
        return text("no_reasons", language)
    return escape(", ".join(translate_reason(factor, language) for factor in factors))
