import inspect
import logging
from collections.abc import Awaitable, Callable, Iterable
from datetime import UTC, datetime
from typing import Protocol
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from bot.domain.models import LocationForecast, Subscription, User
from bot.services.report_formatter import FORECAST_PARSE_MODE, format_forecast_report
from bot.services.subscription_service import select_reports_for_subscription

logger = logging.getLogger(__name__)


class SupportsExceptionLogging(Protocol):
    def exception(self, msg: str, *args: object) -> None: ...


ReportsLoader = Callable[
    [Subscription],
    Iterable[LocationForecast] | Awaitable[Iterable[LocationForecast]],
]
MessageSender = Callable[..., object | Awaitable[object]]
UserLoader = Callable[[int], User | None]


def build_subscription_message(
    subscription: Subscription,
    reports: Iterable[LocationForecast],
    language: str = "en",
) -> str | None:
    selected = select_reports_for_subscription(
        reports,
        subscription.mode,
        subscription.score_threshold,
    )

    if not selected:
        return None

    return format_forecast_report(selected, language=language)


async def send_due_subscriptions(
    subscriptions: Iterable[Subscription],
    load_reports: ReportsLoader,
    send_message: MessageSender,
    load_user: UserLoader | None = None,
    log: SupportsExceptionLogging | None = None,
) -> None:
    active_log = log or logger

    for subscription in subscriptions:
        if not subscription.enabled:
            continue

        try:
            reports = await _maybe_await(load_reports(subscription))
            user = load_user(subscription.user_id) if load_user else None
            language = user.language if user else "en"
            message = build_subscription_message(subscription, reports, language=language)
            if message is None:
                continue

            await _maybe_await(
                send_message(subscription.user_id, message, parse_mode=FORECAST_PARSE_MODE)
            )
        except Exception:
            active_log.exception(
                "Failed to send subscription forecast for user_id=%s",
                subscription.user_id,
            )


def due_subscriptions(
    subscriptions: Iterable[Subscription],
    load_user: UserLoader,
    now_utc: datetime | None = None,
) -> list[Subscription]:
    current_utc = now_utc or datetime.now(tz=UTC)
    due = []

    for subscription in subscriptions:
        user = load_user(subscription.user_id)
        timezone = _safe_timezone(user.timezone if user else "UTC")
        local_now = current_utc.astimezone(timezone)
        if (
            local_now.hour == subscription.send_time_local.hour
            and local_now.minute == subscription.send_time_local.minute
        ):
            due.append(subscription)

    return due


async def _maybe_await[T](value: T | Awaitable[T]) -> T:
    if inspect.isawaitable(value):
        return await value
    return value


def _safe_timezone(timezone: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")
