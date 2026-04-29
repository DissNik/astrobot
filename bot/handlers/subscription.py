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
from bot.texts.i18n import DEFAULT_LANGUAGE

router = Router()

SUBSCRIPTION_TEXT = (
    "Astronomy forecast alerts. You can enable a daily digest or disable sending."
)


@router.message(Command("subscribe"))
@router.message(F.text == "📬 Рассылка")
async def subscribe_command(message: Message) -> None:
    await message.answer(SUBSCRIPTION_TEXT, reply_markup=subscription_keyboard())


@router.callback_query(F.data == "subscription:open")
async def subscription_callback(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.answer(SUBSCRIPTION_TEXT, reply_markup=subscription_keyboard())
    await callback.answer()


@router.callback_query(F.data == "subscription:enable")
async def enable_subscription_callback(
    callback: CallbackQuery,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
    connection: sqlite3.Connection,
) -> None:
    _ensure_user(callback.from_user.id, users)
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
            "Alerts enabled. By default, I send a daily digest at 20:00 UTC.",
            reply_markup=main_menu_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data == "subscription:disable")
async def disable_subscription_callback(
    callback: CallbackQuery,
    users: UserRepository,
    subscriptions: SubscriptionRepository,
    connection: sqlite3.Connection,
) -> None:
    _ensure_user(callback.from_user.id, users)
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
        await callback.message.answer("Alerts disabled.", reply_markup=main_menu_keyboard())
    await callback.answer()


def _ensure_user(user_id: int, users: UserRepository) -> None:
    if users.get(user_id) is not None:
        return

    users.upsert(
        User(
            telegram_id=user_id,
            timezone="UTC",
            language=DEFAULT_LANGUAGE,
            forecast_days=3,
            observing_profile=ObservingProfile.DEEP_SKY,
            score_threshold=60,
            created_at=datetime.now(tz=UTC),
        )
    )
