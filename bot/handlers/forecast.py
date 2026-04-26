from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

router = Router()

FORECAST_TEXT = "Прогноз. Выберите точку наблюдения, чтобы получить астрономический прогноз."


@router.message(Command("forecast"))
async def forecast_command(message: Message) -> None:
    await message.answer(FORECAST_TEXT)


@router.callback_query(F.data == "forecast:open")
async def forecast_callback(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.answer(FORECAST_TEXT)
    await callback.answer()
