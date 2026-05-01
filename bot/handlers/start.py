from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.handlers.common import language_for_message
from bot.keyboards.menu import main_menu_keyboard
from bot.repositories.users import UserRepository
from bot.texts.i18n import text

router = Router()


@router.message(CommandStart())
async def start_command(message: Message, users: UserRepository | None = None) -> None:
    language = language_for_message(message, users)
    await message.answer(
        text("start_text", language),
        reply_markup=main_menu_keyboard(language),
    )
