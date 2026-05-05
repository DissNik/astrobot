import sqlite3

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.domain.enums import SubscriptionMode
from bot.domain.models import Subscription, User
from bot.handlers.common import edit_callback_message, language_for_message, language_for_user
from bot.handlers.menu_format import MENU_PARSE_MODE, format_menu_message
from bot.keyboards.subscription import subscription_keyboard
from bot.repositories.subscriptions import SubscriptionRepository
from bot.repositories.users import UserRepository
from bot.services.subscription_service import (
    build_default_subscription,
    disable_subscription,
    enable_subscription,
)
from bot.services.user_service import build_default_user, ensure_user
from bot.texts.i18n import normalize_language, text

router = Router()


@router.message(Command("subscribe"))
@router.message(F.text == "📬 Рассылка")
@router.message(F.text == "📬 Alerts")
async def subscribe_command(
    message: Message,
    users: UserRepository | None = None,
    subscriptions: SubscriptionRepository | None = None,
) -> None:
    language = language_for_message(message, users)
    user_id = message.from_user.id if message.from_user else None
    await message.answer(
        _format_subscription_menu(user_id, users, subscriptions),
        reply_markup=subscription_keyboard(
            language,
            enabled=_subscription_enabled_for_menu(user_id, subscriptions),
        ),
        parse_mode=MENU_PARSE_MODE,
    )


@router.callback_query(F.data == "subscription:open")
async def subscription_callback(
    callback: CallbackQuery,
    users: UserRepository | None = None,
    subscriptions: SubscriptionRepository | None = None,
) -> None:
    language = language_for_user(callback.from_user.id, users)
    if callback.message:
        await edit_callback_message(
            callback.message,
            _format_subscription_menu(callback.from_user.id, users, subscriptions),
            reply_markup=subscription_keyboard(
                language,
                enabled=_subscription_enabled_for_menu(callback.from_user.id, subscriptions),
            ),
            parse_mode=MENU_PARSE_MODE,
        )
    await callback.answer()


@router.callback_query(F.data == "subscription:enable")
async def enable_subscription_callback(
    callback: CallbackQuery,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
    connection: sqlite3.Connection,
) -> None:
    user = ensure_user(callback.from_user.id, users)
    language = normalize_language(user.language)
    subscription = enable_subscription(user, subscriptions.get(callback.from_user.id))
    subscriptions.upsert(subscription)
    connection.commit()
    if callback.message:
        await edit_callback_message(
            callback.message,
            _format_subscription_menu_for_values(subscription, user.timezone, language),
            reply_markup=subscription_keyboard(language, enabled=subscription.enabled),
            parse_mode=MENU_PARSE_MODE,
        )
    await callback.answer()


@router.callback_query(F.data == "subscription:disable")
async def disable_subscription_callback(
    callback: CallbackQuery,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
    connection: sqlite3.Connection,
) -> None:
    user = ensure_user(callback.from_user.id, users)
    language = normalize_language(user.language)
    subscription = disable_subscription(user, subscriptions.get(callback.from_user.id))
    subscriptions.upsert(subscription)
    connection.commit()
    if callback.message:
        await edit_callback_message(
            callback.message,
            _format_subscription_menu_for_values(subscription, user.timezone, language),
            reply_markup=subscription_keyboard(language, enabled=subscription.enabled),
            parse_mode=MENU_PARSE_MODE,
        )
    await callback.answer()


def _format_subscription_menu(
    user_id: int | None,
    users: UserRepository | None,
    subscriptions: SubscriptionRepository | None,
) -> str:
    language = language_for_user(user_id, users)
    user = users.get(user_id) if user_id is not None and users is not None else None
    subscription = (
        subscriptions.get(user_id)
        if user_id is not None and subscriptions is not None
        else None
    )
    timezone = user.timezone if user else "UTC"
    return _format_subscription_menu_for_values(
        _subscription_for_menu(user_id, user, subscription),
        timezone,
        language,
    )


def _subscription_for_menu(
    user_id: int | None,
    user: User | None,
    subscription: Subscription | None,
) -> Subscription:
    if subscription is not None:
        return subscription

    fallback_user = user or build_default_user(user_id or 0)
    return build_default_subscription(fallback_user)


def _subscription_enabled_for_menu(
    user_id: int | None,
    subscriptions: SubscriptionRepository | None,
) -> bool:
    if user_id is None or subscriptions is None:
        return False

    subscription = subscriptions.get(user_id)
    return subscription.enabled if subscription else False


def _format_subscription_menu_for_values(
    subscription: Subscription,
    timezone: str,
    language: str,
) -> str:
    language = normalize_language(language)
    send_time = subscription.send_time_local.isoformat(timespec="minutes")
    subscription_state = text("enabled" if subscription.enabled else "disabled", language)
    body = (
        f"🔔 {_subscription_label('subscription', language)}: {subscription_state}\n"
        f"🕘 {_subscription_label('time', language)}: {send_time} {timezone}\n"
        f"📬 {_subscription_label('mode', language)}: {_format_mode(subscription.mode, language)}\n"
        f"⭐ {_subscription_label('threshold', language)}: {subscription.score_threshold}/100"
    )
    return format_menu_message("📬", _subscription_label("title", language), body)


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
