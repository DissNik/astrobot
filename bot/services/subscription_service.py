from collections.abc import Iterable
from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from bot.domain.enums import SubscriptionMode
from bot.domain.models import LocationForecast, Subscription, User


def build_default_subscription(
    user: User,
    current: Subscription | None = None,
    now_utc: datetime | None = None,
) -> Subscription:
    now = now_utc or datetime.now(tz=UTC)
    return Subscription(
        user_id=user.telegram_id,
        enabled=current.enabled if current else False,
        mode=current.mode if current else SubscriptionMode.DAILY_DIGEST,
        send_time_local=current.send_time_local if current else time(20, 0),
        forecast_days=current.forecast_days if current else user.forecast_days,
        observing_profile=current.observing_profile if current else user.observing_profile,
        score_threshold=current.score_threshold if current else user.score_threshold,
        updated_at=now,
        last_sent_on=current.last_sent_on if current else None,
    )


def enable_subscription(
    user: User,
    current: Subscription | None,
    now_utc: datetime | None = None,
) -> Subscription:
    now = now_utc or datetime.now(tz=UTC)
    base = build_default_subscription(user, current, now)
    return Subscription(
        user_id=base.user_id,
        enabled=True,
        mode=base.mode,
        send_time_local=base.send_time_local,
        forecast_days=base.forecast_days,
        observing_profile=base.observing_profile,
        score_threshold=base.score_threshold,
        updated_at=now,
        last_sent_on=last_sent_on_for_enabled_subscription(base, user, now),
    )


def disable_subscription(
    user: User,
    current: Subscription | None,
    now_utc: datetime | None = None,
) -> Subscription:
    now = now_utc or datetime.now(tz=UTC)
    base = build_default_subscription(user, current, now)
    return Subscription(
        user_id=base.user_id,
        enabled=False,
        mode=base.mode,
        send_time_local=base.send_time_local,
        forecast_days=base.forecast_days,
        observing_profile=base.observing_profile,
        score_threshold=base.score_threshold,
        updated_at=now,
        last_sent_on=base.last_sent_on,
    )


def last_sent_on_for_enabled_subscription(
    subscription: Subscription,
    user: User,
    now_utc: datetime,
) -> date | None:
    timezone = _safe_timezone(user.timezone)
    local_now = now_utc.astimezone(timezone)
    local_today = local_now.date()
    if subscription.last_sent_on == local_today:
        return subscription.last_sent_on
    if local_now.time().replace(second=0, microsecond=0) >= subscription.send_time_local:
        return local_today
    return subscription.last_sent_on


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


def _safe_timezone(timezone: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")
