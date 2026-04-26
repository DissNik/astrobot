from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards.locations import locations_keyboard

router = Router()

LOCATIONS_TEXT = "Точки наблюдения. Здесь можно будет управлять сохраненными местами."


@router.message(Command("locations"))
async def locations_command(message: Message) -> None:
    await message.answer(LOCATIONS_TEXT, reply_markup=locations_keyboard())


@router.callback_query(F.data == "locations:open")
async def locations_callback(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.answer(LOCATIONS_TEXT, reply_markup=locations_keyboard())
    await callback.answer()


@router.callback_query(F.data.in_({"locations:add", "locations:list"}))
async def locations_placeholder_callback(callback: CallbackQuery) -> None:
    await callback.answer("Управление точками будет доступно в следующем шаге.", show_alert=True)
