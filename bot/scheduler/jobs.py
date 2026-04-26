import inspect
import logging
from collections.abc import Awaitable, Callable, Iterable
from typing import Protocol

from bot.domain.models import LocationForecast, Subscription
from bot.services.report_formatter import format_forecast_report
from bot.services.subscription_service import select_reports_for_subscription

logger = logging.getLogger(__name__)


class SupportsExceptionLogging(Protocol):
    def exception(self, msg: str, *args: object) -> None: ...


ReportsLoader = Callable[
    [Subscription],
    Iterable[LocationForecast] | Awaitable[Iterable[LocationForecast]],
]
MessageSender = Callable[[int, str], object | Awaitable[object]]


def build_subscription_message(
    subscription: Subscription,
    reports: Iterable[LocationForecast],
) -> str | None:
    selected = select_reports_for_subscription(
        reports,
        subscription.mode,
        subscription.score_threshold,
    )

    if not selected:
        return None

    return format_forecast_report(selected)


async def send_due_subscriptions(
    subscriptions: Iterable[Subscription],
    load_reports: ReportsLoader,
    send_message: MessageSender,
    log: SupportsExceptionLogging | None = None,
) -> None:
    active_log = log or logger

    for subscription in subscriptions:
        if not subscription.enabled:
            continue

        try:
            reports = await _maybe_await(load_reports(subscription))
            message = build_subscription_message(subscription, reports)
            if message is None:
                continue

            await _maybe_await(send_message(subscription.user_id, message))
        except Exception:
            active_log.exception(
                "Failed to send subscription forecast for user_id=%s",
                subscription.user_id,
            )


async def _maybe_await[T](value: T | Awaitable[T]) -> T:
    if inspect.isawaitable(value):
        return await value
    return value
