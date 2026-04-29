import sqlite3
from datetime import UTC, datetime, time

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from bot.domain.enums import ObservingProfile, SubscriptionMode
from bot.domain.models import Subscription, User
from bot.keyboards.menu import main_menu_keyboard
from bot.keyboards.settings import settings_keyboard
from bot.repositories.subscriptions import SubscriptionRepository
from bot.repositories.users import UserRepository
from bot.texts.i18n import DEFAULT_LANGUAGE, normalize_language, text

router = Router()


class SettingsStates(StatesGroup):
    waiting_for_send_time = State()


@router.message(Command("settings"))
@router.message(F.text == "⚙️ Настройки")
@router.message(F.text == "⚙️ Settings")
async def settings_command(
    message: Message,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
) -> None:
    user_id = _message_user_id(message)
    language = _language_for_user(user_id, users)
    await message.answer(
        _format_settings(user_id, users, subscriptions, language),
        reply_markup=_settings_keyboard_for_user(user_id, users, subscriptions, language),
    )


@router.callback_query(F.data == "settings:open")
async def settings_callback(
    callback: CallbackQuery,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
) -> None:
    language = _language_for_user(callback.from_user.id, users)
    if callback.message:
        await callback.message.answer(
            _format_settings(callback.from_user.id, users, subscriptions, language),
            reply_markup=_settings_keyboard_for_user(
                callback.from_user.id, users, subscriptions, language
            ),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("settings:language:"))
async def update_language_callback(
    callback: CallbackQuery,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
    connection: sqlite3.Connection,
) -> None:
    raw_language = callback.data.removeprefix("settings:language:") if callback.data else None
    language = normalize_language(raw_language)
    user = _ensure_user(callback.from_user.id, users)
    subscription = _ensure_subscription(user, subscriptions)
    users.upsert(_replace_user_settings(user, language=language))
    subscriptions.upsert(subscription)
    connection.commit()
    await _send_updated_settings(
        callback,
        users,
        subscriptions,
        language,
        refresh_main_menu=True,
    )


@router.callback_query(F.data.startswith("settings:days:"))
async def update_forecast_days_callback(
    callback: CallbackQuery,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
    connection: sqlite3.Connection,
) -> None:
    days = _parse_int_callback_value(callback.data, "settings:days:")
    if days not in {3, 5, 7}:
        await callback.answer("Choose 3, 5, or 7 nights.", show_alert=True)
        return

    user = _ensure_user(callback.from_user.id, users)
    language = user.language
    subscription = _ensure_subscription(user, subscriptions)
    users.upsert(_replace_user_settings(user, forecast_days=days))
    subscriptions.upsert(_replace_subscription_settings(subscription, forecast_days=days))
    connection.commit()
    await _send_updated_settings(
        callback,
        users,
        subscriptions,
        language,
    )


@router.callback_query(F.data.startswith("settings:profile:"))
async def update_profile_callback(
    callback: CallbackQuery,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
    connection: sqlite3.Connection,
) -> None:
    profile = _parse_profile(callback.data)
    if profile is None:
        await callback.answer("Unknown observing profile.", show_alert=True)
        return

    user = _ensure_user(callback.from_user.id, users)
    language = user.language
    subscription = _ensure_subscription(user, subscriptions)
    users.upsert(_replace_user_settings(user, observing_profile=profile))
    subscriptions.upsert(_replace_subscription_settings(subscription, observing_profile=profile))
    connection.commit()
    await _send_updated_settings(
        callback,
        users,
        subscriptions,
        language,
    )


@router.callback_query(F.data.startswith("settings:threshold:"))
async def update_threshold_callback(
    callback: CallbackQuery,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
    connection: sqlite3.Connection,
) -> None:
    threshold = _parse_int_callback_value(callback.data, "settings:threshold:")
    if threshold is None or not 0 <= threshold <= 100:
        await callback.answer("Threshold must be from 0 to 100.", show_alert=True)
        return

    user = _ensure_user(callback.from_user.id, users)
    language = user.language
    subscription = _ensure_subscription(user, subscriptions)
    users.upsert(_replace_user_settings(user, score_threshold=threshold))
    subscriptions.upsert(_replace_subscription_settings(subscription, score_threshold=threshold))
    connection.commit()
    await _send_updated_settings(
        callback,
        users,
        subscriptions,
        language,
    )


@router.callback_query(F.data.startswith("settings:mode:"))
async def update_subscription_mode_callback(
    callback: CallbackQuery,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
    connection: sqlite3.Connection,
) -> None:
    mode = _parse_subscription_mode(callback.data)
    if mode is None:
        await callback.answer("Unknown notification mode.", show_alert=True)
        return

    user = _ensure_user(callback.from_user.id, users)
    language = user.language
    subscription = _ensure_subscription(user, subscriptions)
    users.upsert(user)
    subscriptions.upsert(_replace_subscription_settings(subscription, mode=mode))
    connection.commit()
    await _send_updated_settings(
        callback,
        users,
        subscriptions,
        language,
    )


@router.callback_query(F.data == "settings:time")
async def settings_time_callback(
    callback: CallbackQuery,
    state: FSMContext,
    users: UserRepository,
) -> None:
    await state.set_state(SettingsStates.waiting_for_send_time)
    language = _language_for_user(callback.from_user.id, users)
    if callback.message:
        await callback.message.answer(text("enter_send_time", language))
    await callback.answer()


@router.message(SettingsStates.waiting_for_send_time)
async def settings_time_message(
    message: Message,
    state: FSMContext,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
    connection: sqlite3.Connection,
) -> None:
    send_time = _parse_time(message.text)
    user_id = _message_user_id(message)
    language = _language_for_user(user_id, users)
    if send_time is None:
        await message.answer(text("invalid_send_time", language))
        return

    if user_id is None:
        await message.answer(text("invalid_send_time", language))
        return

    user = _ensure_user(user_id, users)
    subscription = _ensure_subscription(user, subscriptions)
    users.upsert(user)
    subscriptions.upsert(_replace_subscription_settings(subscription, send_time_local=send_time))
    connection.commit()
    await state.clear()
    await message.answer(
        text("send_time_updated", language)
        + "\n\n"
        + _format_settings(user_id, users, subscriptions, language),
        reply_markup=_settings_keyboard_for_user(user_id, users, subscriptions, language),
    )


def _format_settings(
    user_id: int | None,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    language = normalize_language(language)
    if user_id is None:
        return text("settings_title", language)

    user = users.get(user_id)
    subscription = subscriptions.get(user_id)
    forecast_days = user.forecast_days if user else 3
    profile = user.observing_profile if user else ObservingProfile.DEEP_SKY
    threshold = subscription.score_threshold if subscription else 60
    send_time = (
        subscription.send_time_local.isoformat(timespec="minutes") if subscription else "20:00"
    )
    mode = subscription.mode if subscription else SubscriptionMode.DAILY_DIGEST
    enabled = subscription.enabled if subscription else False

    subscription_state = text("enabled" if enabled else "disabled", language)
    return (
        f"⚙️ {text('settings_title', language).rstrip('.')}\n\n"
        f"🌙 {_settings_label('forecast', language)}: {forecast_days} {text('nights', language)}\n"
        f"🔭 {_settings_label('profile', language)}: {_format_profile(profile, language)}\n"
        f"🔔 {_settings_label('subscription', language)}: {subscription_state}\n"
        f"🕘 {_settings_label('time', language)}: {send_time}\n"
        f"📬 {_settings_label('mode', language)}: {_format_mode(mode, language)}\n"
        f"⭐ {_settings_label('threshold', language)}: {threshold}/100"
    )


def _message_user_id(message: Message) -> int | None:
    if message.from_user is None:
        return None
    return message.from_user.id


def _format_profile(profile: ObservingProfile, language: str) -> str:
    return {
        ObservingProfile.DEEP_SKY: text("settings_profile_deep_sky", language),
        ObservingProfile.PLANETARY_LUNAR: text("settings_profile_planetary_lunar", language),
    }[profile]


def _format_mode(mode: SubscriptionMode, language: str) -> str:
    return {
        SubscriptionMode.DAILY_DIGEST: text("settings_daily_digest", language),
        SubscriptionMode.GOOD_CONDITIONS_ONLY: text("settings_good_conditions_only", language),
    }[mode]


def _settings_label(key: str, language: str) -> str:
    labels = {
        "en": {
            "forecast": "Forecast",
            "profile": "Profile",
            "subscription": "Subscription",
            "time": "Time",
            "mode": "Mode",
            "threshold": "Threshold",
        },
        "ru": {
            "forecast": "Прогноз",
            "profile": "Профиль",
            "subscription": "Рассылка",
            "time": "Время",
            "mode": "Режим",
            "threshold": "Порог",
        },
    }
    return labels[normalize_language(language)][key]


async def _send_updated_settings(
    callback: CallbackQuery,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
    language: str,
    refresh_main_menu: bool = False,
) -> None:
    if callback.message:
        settings_text = _format_settings(callback.from_user.id, users, subscriptions, language)
        try:
            await callback.message.edit_text(
                settings_text,
                reply_markup=_settings_keyboard_for_user(
                    callback.from_user.id, users, subscriptions, language
                ),
            )
        except TelegramBadRequest as error:
            if "message is not modified" not in str(error):
                raise
        if refresh_main_menu:
            menu_message = await callback.message.answer(
                "\u2060",
                reply_markup=main_menu_keyboard(language),
            )
            await menu_message.delete()
    await callback.answer()


def _settings_keyboard_for_user(
    user_id: int | None,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
    language: str,
) -> InlineKeyboardMarkup:
    user = users.get(user_id) if user_id is not None else None
    subscription = subscriptions.get(user_id) if user_id is not None else None
    return settings_keyboard(
        language,
        selected_language=user.language if user else language,
        forecast_days=user.forecast_days if user else 3,
        observing_profile=user.observing_profile if user else ObservingProfile.DEEP_SKY,
        mode=subscription.mode if subscription else SubscriptionMode.DAILY_DIGEST,
        score_threshold=subscription.score_threshold if subscription else 60,
    )


def _ensure_user(user_id: int, users: UserRepository) -> User:
    user = users.get(user_id)
    if user is not None:
        return user

    return User(
        telegram_id=user_id,
        timezone="UTC",
        language=DEFAULT_LANGUAGE,
        forecast_days=3,
        observing_profile=ObservingProfile.DEEP_SKY,
        score_threshold=60,
        created_at=datetime.now(tz=UTC),
    )


def _ensure_subscription(user: User, subscriptions: SubscriptionRepository) -> Subscription:
    subscription = subscriptions.get(user.telegram_id)
    if subscription is not None:
        return subscription

    return Subscription(
        user_id=user.telegram_id,
        enabled=False,
        mode=SubscriptionMode.DAILY_DIGEST,
        send_time_local=time(20, 0),
        forecast_days=user.forecast_days,
        observing_profile=user.observing_profile,
        score_threshold=user.score_threshold,
        updated_at=datetime.now(tz=UTC),
    )


def _replace_user_settings(
    user: User,
    forecast_days: int | None = None,
    observing_profile: ObservingProfile | None = None,
    score_threshold: int | None = None,
    language: str | None = None,
) -> User:
    return User(
        telegram_id=user.telegram_id,
        timezone=user.timezone,
        language=normalize_language(language or user.language),
        forecast_days=forecast_days if forecast_days is not None else user.forecast_days,
        observing_profile=observing_profile or user.observing_profile,
        score_threshold=score_threshold if score_threshold is not None else user.score_threshold,
        created_at=user.created_at,
    )


def _replace_subscription_settings(
    subscription: Subscription,
    forecast_days: int | None = None,
    observing_profile: ObservingProfile | None = None,
    score_threshold: int | None = None,
    mode: SubscriptionMode | None = None,
    send_time_local: time | None = None,
) -> Subscription:
    return Subscription(
        user_id=subscription.user_id,
        enabled=subscription.enabled,
        mode=mode or subscription.mode,
        send_time_local=send_time_local or subscription.send_time_local,
        forecast_days=forecast_days if forecast_days is not None else subscription.forecast_days,
        observing_profile=observing_profile or subscription.observing_profile,
        score_threshold=(
            score_threshold if score_threshold is not None else subscription.score_threshold
        ),
        updated_at=datetime.now(tz=UTC),
    )


def _parse_int_callback_value(data: str | None, prefix: str) -> int | None:
    if data is None or not data.startswith(prefix):
        return None
    try:
        return int(data.removeprefix(prefix))
    except ValueError:
        return None


def _parse_profile(data: str | None) -> ObservingProfile | None:
    if data is None or not data.startswith("settings:profile:"):
        return None
    try:
        return ObservingProfile(data.removeprefix("settings:profile:"))
    except ValueError:
        return None


def _parse_subscription_mode(data: str | None) -> SubscriptionMode | None:
    if data is None or not data.startswith("settings:mode:"):
        return None
    try:
        return SubscriptionMode(data.removeprefix("settings:mode:"))
    except ValueError:
        return None


def _parse_time(text: str | None) -> time | None:
    if text is None:
        return None
    try:
        return time.fromisoformat(text.strip())
    except ValueError:
        return None


def _language_for_user(user_id: int | None, users: UserRepository) -> str:
    if user_id is None:
        return DEFAULT_LANGUAGE
    user = users.get(user_id)
    if user is None:
        return DEFAULT_LANGUAGE
    return normalize_language(user.language)
