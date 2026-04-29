import inspect
import logging
from collections.abc import Awaitable, Callable, Iterable
from datetime import UTC, date, datetime
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
SentMarker = Callable[[Subscription, date], object | Awaitable[object]]


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
    mark_sent: SentMarker | None = None,
    now_utc: datetime | None = None,
    log: SupportsExceptionLogging | None = None,
) -> None:
    active_log = log or logger
    current_utc = now_utc or datetime.now(tz=UTC)

    for subscription in subscriptions:
        if not subscription.enabled:
            continue

        try:
            reports = await _maybe_await(load_reports(subscription))
            user = load_user(subscription.user_id) if load_user else None
            language = user.language if user else "en"
            message = build_subscription_message(subscription, reports, language=language)
            if message is None:
                await _mark_subscription_processed(subscription, user, current_utc, mark_sent)
                continue

            await _maybe_await(
                send_message(subscription.user_id, message, parse_mode=FORECAST_PARSE_MODE)
            )
            await _mark_subscription_processed(subscription, user, current_utc, mark_sent)
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
        local_today = local_now.date()
        if subscription.last_sent_on == local_today:
            continue
        if local_now.time().replace(second=0, microsecond=0) >= subscription.send_time_local:
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


def _subscription_local_date(
    subscription: Subscription,
    user: User | None,
    current_utc: datetime,
) -> date:
    timezone = _safe_timezone(user.timezone if user else "UTC")
    return current_utc.astimezone(timezone).date()


async def _mark_subscription_processed(
    subscription: Subscription,
    user: User | None,
    current_utc: datetime,
    mark_sent: SentMarker | None,
) -> None:
    if mark_sent is None:
        return

    sent_on = _subscription_local_date(subscription, user, current_utc)
    await _maybe_await(mark_sent(subscription, sent_on))
