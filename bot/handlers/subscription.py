import sqlite3
from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.domain.enums import ObservingProfile, SubscriptionMode
from bot.domain.models import Subscription, User
from bot.keyboards.subscription import subscription_keyboard
from bot.repositories.subscriptions import SubscriptionRepository
from bot.repositories.users import UserRepository
from bot.texts.i18n import DEFAULT_LANGUAGE, normalize_language, text

router = Router()


@router.message(Command("subscribe"))
@router.message(F.text == "📬 Рассылка")
@router.message(F.text == "📬 Alerts")
async def subscribe_command(
    message: Message,
    users: UserRepository | None = None,
    subscriptions: SubscriptionRepository | None = None,
) -> None:
    language = _language_for_message(message, users)
    user_id = message.from_user.id if message.from_user else None
    await message.answer(
        _format_subscription_menu(user_id, users, subscriptions),
        reply_markup=subscription_keyboard(language),
    )


@router.callback_query(F.data == "subscription:open")
async def subscription_callback(
    callback: CallbackQuery,
    users: UserRepository | None = None,
    subscriptions: SubscriptionRepository | None = None,
) -> None:
    language = _language_for_user(callback.from_user.id, users)
    if callback.message:
        await _edit_callback_message(
            callback.message,
            _format_subscription_menu(callback.from_user.id, users, subscriptions),
            reply_markup=subscription_keyboard(language),
        )
    await callback.answer()


@router.callback_query(F.data == "subscription:enable")
async def enable_subscription_callback(
    callback: CallbackQuery,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
    connection: sqlite3.Connection,
) -> None:
    user = _ensure_user(callback.from_user.id, users)
    language = normalize_language(user.language)
    now = datetime.now(tz=UTC)
    current = subscriptions.get(callback.from_user.id)
    send_time_local = current.send_time_local if current else time(20, 0)
    base_subscription = Subscription(
        user_id=callback.from_user.id,
        enabled=current.enabled if current else False,
        mode=current.mode if current else SubscriptionMode.DAILY_DIGEST,
        send_time_local=send_time_local,
        forecast_days=current.forecast_days if current else 3,
        observing_profile=current.observing_profile if current else ObservingProfile.DEEP_SKY,
        score_threshold=current.score_threshold if current else 60,
        updated_at=now,
        last_sent_on=current.last_sent_on if current else None,
    )
    subscription = Subscription(
        user_id=callback.from_user.id,
        enabled=True,
        mode=base_subscription.mode,
        send_time_local=base_subscription.send_time_local,
        forecast_days=base_subscription.forecast_days,
        observing_profile=base_subscription.observing_profile,
        score_threshold=base_subscription.score_threshold,
        updated_at=now,
        last_sent_on=_last_sent_on_for_enabled_subscription(base_subscription, user, now),
    )
    subscriptions.upsert(subscription)
    connection.commit()
    if callback.message:
        await _edit_callback_message(
            callback.message,
            _format_subscription_menu_for_values(subscription, user.timezone, language),
            reply_markup=subscription_keyboard(language),
        )
    await callback.answer()


@router.callback_query(F.data == "subscription:disable")
async def disable_subscription_callback(
    callback: CallbackQuery,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
    connection: sqlite3.Connection,
) -> None:
    user = _ensure_user(callback.from_user.id, users)
    language = normalize_language(user.language)
    now = datetime.now(tz=UTC)
    current = subscriptions.get(callback.from_user.id)
    subscription = Subscription(
        user_id=callback.from_user.id,
        enabled=False,
        mode=current.mode if current else SubscriptionMode.DAILY_DIGEST,
        send_time_local=current.send_time_local if current else time(20, 0),
        forecast_days=current.forecast_days if current else 3,
        observing_profile=current.observing_profile if current else ObservingProfile.DEEP_SKY,
        score_threshold=current.score_threshold if current else 60,
        updated_at=now,
        last_sent_on=current.last_sent_on if current else None,
    )
    subscriptions.upsert(subscription)
    connection.commit()
    if callback.message:
        await _edit_callback_message(
            callback.message,
            _format_subscription_menu_for_values(subscription, user.timezone, language),
            reply_markup=subscription_keyboard(language),
        )
    await callback.answer()


def _ensure_user(user_id: int, users: UserRepository) -> User:
    user = users.get(user_id)
    if user is not None:
        return user

    user = User(
        telegram_id=user_id,
        timezone="UTC",
        language=DEFAULT_LANGUAGE,
        forecast_days=3,
        observing_profile=ObservingProfile.DEEP_SKY,
        score_threshold=60,
        created_at=datetime.now(tz=UTC),
    )
    users.upsert(user)
    return user


def _last_sent_on_for_enabled_subscription(
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


def _safe_timezone(timezone: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _format_subscription_menu(
    user_id: int | None,
    users: UserRepository | None,
    subscriptions: SubscriptionRepository | None,
) -> str:
    language = _language_for_user(user_id, users) if user_id is not None else DEFAULT_LANGUAGE
    user = users.get(user_id) if user_id is not None and users is not None else None
    subscription = (
        subscriptions.get(user_id)
        if user_id is not None and subscriptions is not None
        else None
    )
    timezone = user.timezone if user else "UTC"
    if subscription is None:
        subscription = Subscription(
            user_id=user_id or 0,
            enabled=False,
            mode=SubscriptionMode.DAILY_DIGEST,
            send_time_local=time(20, 0),
            forecast_days=3,
            observing_profile=ObservingProfile.DEEP_SKY,
            score_threshold=60,
            updated_at=datetime.now(tz=UTC),
        )
    return _format_subscription_menu_for_values(subscription, timezone, language)


def _format_subscription_menu_for_values(
    subscription: Subscription,
    timezone: str,
    language: str,
) -> str:
    language = normalize_language(language)
    send_time = subscription.send_time_local.isoformat(timespec="minutes")
    subscription_state = text("enabled" if subscription.enabled else "disabled", language)
    return (
        f"📬 {_subscription_label('title', language)}\n\n"
        f"🔔 {_subscription_label('subscription', language)}: {subscription_state}\n"
        f"🕘 {_subscription_label('time', language)}: {send_time} {timezone}\n"
        f"📬 {_subscription_label('mode', language)}: {_format_mode(subscription.mode, language)}\n"
        f"⭐ {_subscription_label('threshold', language)}: {subscription.score_threshold}/100"
    )


def _format_mode(mode: SubscriptionMode, language: str) -> str:
    return {
        SubscriptionMode.DAILY_DIGEST: text("settings_daily_digest", language),
        SubscriptionMode.GOOD_CONDITIONS_ONLY: text("settings_good_conditions_only", language),
    }[mode]


def _subscription_label(key: str, language: str) -> str:
    labels = {
        "en": {
            "title": "Alerts",
            "subscription": "Subscription",
            "time": "Time",
            "mode": "Mode",
            "threshold": "Threshold",
        },
        "ru": {
            "title": "Рассылка",
            "subscription": "Рассылка",
            "time": "Время",
            "mode": "Режим",
            "threshold": "Порог",
        },
    }
    return labels[normalize_language(language)][key]


async def _edit_callback_message(message: Message, text_value: str, reply_markup=None) -> None:  # noqa: ANN001
    try:
        await message.edit_text(text_value, reply_markup=reply_markup)
    except TelegramBadRequest as error:
        if "message is not modified" not in str(error):
            raise


def _language_for_message(message: Message, users: UserRepository | None) -> str:
    if message.from_user is None:
        return DEFAULT_LANGUAGE
    return _language_for_user(message.from_user.id, users)


def _language_for_user(user_id: int, users: UserRepository | None) -> str:
    if users is None:
        return DEFAULT_LANGUAGE
    user = users.get(user_id)
    if user is None:
        return DEFAULT_LANGUAGE
    return normalize_language(user.language)
