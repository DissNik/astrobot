import sqlite3
from datetime import UTC, datetime, time

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.domain.enums import ObservingProfile, SubscriptionMode
from bot.domain.models import Subscription, User
from bot.keyboards.menu import main_menu_keyboard
from bot.keyboards.subscription import subscription_keyboard
from bot.repositories.subscriptions import SubscriptionRepository
from bot.repositories.users import UserRepository
from bot.texts.i18n import DEFAULT_LANGUAGE, normalize_language, text

router = Router()


@router.message(Command("subscribe"))
@router.message(F.text == "📬 Рассылка")
@router.message(F.text == "📬 Alerts")
async def subscribe_command(message: Message, users: UserRepository | None = None) -> None:
    language = _language_for_message(message, users)
    await message.answer(
        text("subscription_text", language), reply_markup=subscription_keyboard(language)
    )


@router.callback_query(F.data == "subscription:open")
async def subscription_callback(
    callback: CallbackQuery, users: UserRepository | None = None
) -> None:
    language = _language_for_user(callback.from_user.id, users)
    if callback.message:
        await callback.message.answer(
            text("subscription_text", language),
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
    subscriptions.upsert(
        Subscription(
            user_id=callback.from_user.id,
            enabled=True,
            mode=current.mode if current else SubscriptionMode.DAILY_DIGEST,
            send_time_local=current.send_time_local if current else time(20, 0),
            forecast_days=current.forecast_days if current else 3,
            observing_profile=current.observing_profile if current else ObservingProfile.DEEP_SKY,
            score_threshold=current.score_threshold if current else 60,
            updated_at=now,
        )
    )
    connection.commit()
    if callback.message:
        await callback.message.answer(
            text("subscription_enabled_message", language),
            reply_markup=main_menu_keyboard(language),
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
    subscriptions.upsert(
        Subscription(
            user_id=callback.from_user.id,
            enabled=False,
            mode=current.mode if current else SubscriptionMode.DAILY_DIGEST,
            send_time_local=current.send_time_local if current else time(20, 0),
            forecast_days=current.forecast_days if current else 3,
            observing_profile=current.observing_profile if current else ObservingProfile.DEEP_SKY,
            score_threshold=current.score_threshold if current else 60,
            updated_at=now,
        )
    )
    connection.commit()
    if callback.message:
        await callback.message.answer(
            text("subscription_disabled_message", language),
            reply_markup=main_menu_keyboard(language),
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
