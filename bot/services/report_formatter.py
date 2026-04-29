from html import escape

from bot.domain.models import LocationForecast
from bot.texts.i18n import text, translate_reason, translate_verdict

FORECAST_PARSE_MODE = "HTML"
DAY_SEPARATOR = "━━━━━━━━━━━━"


def format_forecast_report(reports: list[LocationForecast], language: str = "en") -> str:
    title = text("forecast_title", language)
    lines = [f"🔭 <b>{escape(title)}</b>"]
    reports_with_nights = [report for report in reports if report.nights]

    if not reports_with_nights:
        return f"🔭 <b>{escape(title)}</b>\n{text('no_forecasts', language)}"

    for report in reports_with_nights:
        lines.append("")
        lines.append(f"📍 <b>{text('location', language)}:</b> {escape(report.location.name)}")

        for night in report.nights:
            moon_percent = round(night.moon_phase * 100)
            moon_visibility = (
                text("visible", language) if night.moon_visible else text("not_visible", language)
            )
            lines.extend(
                [
                    "",
                    DAY_SEPARATOR,
                    (
                        f"📅 <b>{night.night:%Y-%m-%d}</b> — "
                        f"<b>{night.score}/100</b>, "
                        f"{escape(translate_verdict(night.verdict, language))}"
                    ),
                    (
                        f"☁️ <b>{text('cloud_cover', language)}:</b> {night.cloud_cover}% "
                        f"({text('high_cloud_cover', language)}: {night.high_cloud_cover}%)"
                    ),
                    f"🌙 <b>{text('moon', language)}:</b> {moon_percent}%, {moon_visibility}",
                    f"💧 <b>{text('humidity', language)}:</b> {night.humidity}%",
                    f"💨 <b>{text('wind', language)}:</b> {night.wind_speed:.1f} m/s",
                    (
                        f"📝 <b>{text('reasons', language)}:</b> "
                        f"{_format_reasons(night.reasons, language)}"
                    ),
                ]
            )

    return "\n".join(lines)


def _format_reasons(reasons: tuple[str, ...], language: str) -> str:
    if not reasons:
        return text("no_reasons", language)
    return escape(", ".join(translate_reason(reason, language) for reason in reasons))
