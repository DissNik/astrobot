from html import escape

from bot.domain.models import LocationForecast
from bot.texts.ru import FORECAST_TITLE

FORECAST_PARSE_MODE = "HTML"
DAY_SEPARATOR = "━━━━━━━━━━━━"


def format_forecast_report(reports: list[LocationForecast]) -> str:
    lines = [f"🔭 <b>{escape(FORECAST_TITLE)}</b>"]
    reports_with_nights = [report for report in reports if report.nights]

    if not reports_with_nights:
        return f"🔭 <b>{escape(FORECAST_TITLE)}</b>\nНет доступных прогнозов."

    for report in reports_with_nights:
        lines.append("")
        lines.append(f"📍 <b>Локация:</b> {escape(report.location.name)}")

        for night in report.nights:
            moon_percent = round(night.moon_phase * 100)
            moon_visibility = "видна" if night.moon_visible else "не видна"
            lines.extend(
                [
                    "",
                    DAY_SEPARATOR,
                    (
                        f"📅 <b>{night.night:%Y-%m-%d}</b> — "
                        f"<b>{night.score}/100</b>, {escape(night.verdict)}"
                    ),
                    (
                        f"☁️ <b>Облачность:</b> {night.cloud_cover}% "
                        f"(высокая: {night.high_cloud_cover}%)"
                    ),
                    f"🌙 <b>Луна:</b> {moon_percent}%, {moon_visibility}",
                    f"💧 <b>Влажность:</b> {night.humidity}%",
                    f"💨 <b>Ветер:</b> {night.wind_speed:.1f} м/с",
                    f"📝 <b>Причины:</b> {_format_reasons(night.reasons)}",
                ]
            )

    return "\n".join(lines)


def _format_reasons(reasons: tuple[str, ...]) -> str:
    if not reasons:
        return "нет заметных факторов"
    return escape(", ".join(reasons))
