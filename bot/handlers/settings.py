from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

router = Router()

SETTINGS_TEXT = "Настройки. Здесь можно будет изменить параметры бота."


@router.message(Command("settings"))
async def settings_command(message: Message) -> None:
    await message.answer(SETTINGS_TEXT)


@router.callback_query(F.data == "settings:open")
async def settings_callback(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.answer(SETTINGS_TEXT)
    await callback.answer()
