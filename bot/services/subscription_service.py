from collections.abc import Iterable

from bot.domain.enums import SubscriptionMode
from bot.domain.models import LocationForecast


def select_reports_for_subscription(
    reports: Iterable[LocationForecast],
    mode: SubscriptionMode | str,
    threshold: int,
) -> list[LocationForecast]:
    mode = _normalize_mode(mode)
    if not 0 <= threshold <= 100:
        raise ValueError("threshold must be between 0 and 100")

    if mode is SubscriptionMode.DAILY_DIGEST:
        return list(reports)

    return [
        LocationForecast(
            location=report.location,
            nights=[night for night in report.nights if night.score >= threshold],
        )
        for report in reports
        if any(night.score >= threshold for night in report.nights)
    ]


def _normalize_mode(mode: SubscriptionMode | str) -> SubscriptionMode:
    try:
        return SubscriptionMode(mode)
    except ValueError as error:
        raise ValueError("mode must be a valid SubscriptionMode") from error
