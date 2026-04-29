from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.keyboards.menu import main_menu_keyboard
from bot.texts.i18n import DEFAULT_LANGUAGE, text

router = Router()


@router.message(CommandStart())
async def start_command(message: Message) -> None:
    await message.answer(
        text("start_text", DEFAULT_LANGUAGE),
        reply_markup=main_menu_keyboard(DEFAULT_LANGUAGE),
    )
