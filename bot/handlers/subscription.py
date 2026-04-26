from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards.subscription import subscription_keyboard

router = Router()

SUBSCRIPTION_TEXT = "Рассылка. Здесь можно будет настроить ежедневные уведомления."


@router.message(Command("subscribe"))
async def subscribe_command(message: Message) -> None:
    await message.answer(SUBSCRIPTION_TEXT, reply_markup=subscription_keyboard())


@router.callback_query(F.data == "subscription:open")
async def subscription_callback(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.answer(SUBSCRIPTION_TEXT, reply_markup=subscription_keyboard())
    await callback.answer()


@router.callback_query(F.data.in_({"subscription:enable", "subscription:disable"}))
async def subscription_placeholder_callback(callback: CallbackQuery) -> None:
    await callback.answer("Настройка рассылки будет доступна в следующем шаге.", show_alert=True)
