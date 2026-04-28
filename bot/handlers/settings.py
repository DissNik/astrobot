import sqlite3
from datetime import UTC, datetime, time

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.domain.enums import ObservingProfile, SubscriptionMode
from bot.domain.models import Subscription, User
from bot.keyboards.settings import settings_keyboard
from bot.repositories.subscriptions import SubscriptionRepository
from bot.repositories.users import UserRepository

router = Router()

SETTINGS_TEXT = "Настройки профиля и рассылки."
INVALID_TIME_TEXT = "Не смог разобрать время. Введите время в формате HH:MM, например 21:30."


class SettingsStates(StatesGroup):
    waiting_for_send_time = State()


@router.message(Command("settings"))
@router.message(F.text == "⚙️ Настройки")
async def settings_command(
    message: Message,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
) -> None:
    user_id = _message_user_id(message)
    await message.answer(
        _format_settings(user_id, users, subscriptions),
        reply_markup=settings_keyboard(),
    )


@router.callback_query(F.data == "settings:open")
async def settings_callback(
    callback: CallbackQuery,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
) -> None:
    if callback.message:
        await callback.message.answer(
            _format_settings(callback.from_user.id, users, subscriptions),
            reply_markup=settings_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("settings:days:"))
async def update_forecast_days_callback(
    callback: CallbackQuery,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
    connection: sqlite3.Connection,
) -> None:
    days = _parse_int_callback_value(callback.data, "settings:days:")
    if days not in {3, 5, 7}:
        await callback.answer("Выберите 3, 5 или 7 ночей.", show_alert=True)
        return

    user = _ensure_user(callback.from_user.id, users)
    subscription = _ensure_subscription(user, subscriptions)
    users.upsert(_replace_user_settings(user, forecast_days=days))
    subscriptions.upsert(_replace_subscription_settings(subscription, forecast_days=days))
    connection.commit()
    await _send_updated_settings(callback, users, subscriptions, "Горизонт прогноза обновлен.")


@router.callback_query(F.data.startswith("settings:profile:"))
async def update_profile_callback(
    callback: CallbackQuery,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
    connection: sqlite3.Connection,
) -> None:
    profile = _parse_profile(callback.data)
    if profile is None:
        await callback.answer("Неизвестный профиль наблюдений.", show_alert=True)
        return

    user = _ensure_user(callback.from_user.id, users)
    subscription = _ensure_subscription(user, subscriptions)
    users.upsert(_replace_user_settings(user, observing_profile=profile))
    subscriptions.upsert(_replace_subscription_settings(subscription, observing_profile=profile))
    connection.commit()
    await _send_updated_settings(callback, users, subscriptions, "Профиль наблюдений обновлен.")


@router.callback_query(F.data.startswith("settings:threshold:"))
async def update_threshold_callback(
    callback: CallbackQuery,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
    connection: sqlite3.Connection,
) -> None:
    threshold = _parse_int_callback_value(callback.data, "settings:threshold:")
    if threshold is None or not 0 <= threshold <= 100:
        await callback.answer("Порог должен быть от 0 до 100.", show_alert=True)
        return

    user = _ensure_user(callback.from_user.id, users)
    subscription = _ensure_subscription(user, subscriptions)
    users.upsert(_replace_user_settings(user, score_threshold=threshold))
    subscriptions.upsert(_replace_subscription_settings(subscription, score_threshold=threshold))
    connection.commit()
    await _send_updated_settings(callback, users, subscriptions, "Порог хороших условий обновлен.")


@router.callback_query(F.data.startswith("settings:mode:"))
async def update_subscription_mode_callback(
    callback: CallbackQuery,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
    connection: sqlite3.Connection,
) -> None:
    mode = _parse_subscription_mode(callback.data)
    if mode is None:
        await callback.answer("Неизвестный режим рассылки.", show_alert=True)
        return

    user = _ensure_user(callback.from_user.id, users)
    subscription = _ensure_subscription(user, subscriptions)
    users.upsert(user)
    subscriptions.upsert(_replace_subscription_settings(subscription, mode=mode))
    connection.commit()
    await _send_updated_settings(callback, users, subscriptions, "Режим рассылки обновлен.")


@router.callback_query(F.data == "settings:time")
async def settings_time_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SettingsStates.waiting_for_send_time)
    if callback.message:
        await callback.message.answer("Введите время рассылки в формате HH:MM.")
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
    if send_time is None:
        await message.answer(INVALID_TIME_TEXT)
        return

    user_id = _message_user_id(message)
    if user_id is None:
        await message.answer(INVALID_TIME_TEXT)
        return

    user = _ensure_user(user_id, users)
    subscription = _ensure_subscription(user, subscriptions)
    users.upsert(user)
    subscriptions.upsert(_replace_subscription_settings(subscription, send_time_local=send_time))
    connection.commit()
    await state.clear()
    await message.answer(
        "Время рассылки обновлено.\n\n" + _format_settings(user_id, users, subscriptions),
        reply_markup=settings_keyboard(),
    )


def _format_settings(
    user_id: int | None,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
) -> str:
    if user_id is None:
        return SETTINGS_TEXT

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

    return (
        f"{SETTINGS_TEXT}\n"
        f"Горизонт прогноза: {forecast_days} ночи\n"
        f"Профиль наблюдений: {_format_profile(profile)}\n"
        f"Рассылка: {'включена' if enabled else 'отключена'}\n"
        f"Время рассылки: {send_time}\n"
        f"Режим рассылки: {_format_mode(mode)}\n"
        f"Порог хороших условий: {threshold}/100"
    )


def _message_user_id(message: Message) -> int | None:
    if message.from_user is None:
        return None
    return message.from_user.id


def _format_profile(profile: ObservingProfile) -> str:
    return {
        ObservingProfile.DEEP_SKY: "deep-sky",
        ObservingProfile.PLANETARY_LUNAR: "планеты/Луна",
    }[profile]


def _format_mode(mode: SubscriptionMode) -> str:
    return {
        SubscriptionMode.DAILY_DIGEST: "ежедневный дайджест",
        SubscriptionMode.GOOD_CONDITIONS_ONLY: "только хорошие условия",
    }[mode]


async def _send_updated_settings(
    callback: CallbackQuery,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
    message: str,
) -> None:
    if callback.message:
        await callback.message.answer(
            f"{message}\n\n{_format_settings(callback.from_user.id, users, subscriptions)}",
            reply_markup=settings_keyboard(),
        )
    await callback.answer()


def _ensure_user(user_id: int, users: UserRepository) -> User:
    user = users.get(user_id)
    if user is not None:
        return user

    return User(
        telegram_id=user_id,
        timezone="UTC",
        language="ru",
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
) -> User:
    return User(
        telegram_id=user.telegram_id,
        timezone=user.timezone,
        language=user.language,
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
