from collections.abc import Iterable

from bot.domain.enums import SubscriptionMode
from bot.domain.models import LocationForecast


def select_reports_for_subscription(
    reports: Iterable[LocationForecast],
    mode: SubscriptionMode,
    threshold: int,
) -> list[LocationForecast]:
    if mode is SubscriptionMode.DAILY_DIGEST:
        return list(reports)

    return [
        report
        for report in reports
        if any(night.score >= threshold for night in report.nights)
    ]
