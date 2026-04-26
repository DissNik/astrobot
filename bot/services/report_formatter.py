from bot.domain.models import LocationForecast
from bot.texts.ru import FORECAST_TITLE


def format_forecast_report(reports: list[LocationForecast]) -> str:
    lines = [FORECAST_TITLE]

    for report in reports:
        lines.append("")
        lines.append(report.location.name)

        for night in report.nights:
            moon_percent = round(night.moon_phase * 100)
            moon_visibility = "видна" if night.moon_visible else "не видна"
            lines.extend(
                [
                    f"{night.night:%Y-%m-%d}: {night.score}/100, {night.verdict}",
                    f"Облачность: {night.cloud_cover}% (высокая: {night.high_cloud_cover}%)",
                    f"Луна: {moon_percent}%, {moon_visibility}",
                    f"Влажность: {night.humidity}%",
                    f"Ветер: {night.wind_speed:.1f} м/с",
                    f"Причины: {_format_reasons(night.reasons)}",
                ]
            )

    return "\n".join(lines)


def _format_reasons(reasons: tuple[str, ...]) -> str:
    if not reasons:
        return "нет заметных факторов"
    return ", ".join(reasons)
