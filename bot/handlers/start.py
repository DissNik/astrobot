from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.keyboards.menu import main_menu_keyboard

router = Router()

MENU_TEXT = "Привет! Я помогу выбрать время для астрономической поездки."


@router.message(CommandStart())
async def start_command(message: Message) -> None:
    await message.answer(MENU_TEXT, reply_markup=main_menu_keyboard())
