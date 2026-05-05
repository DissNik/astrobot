from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.handlers.menu_format import MENU_PARSE_MODE, format_menu_message
from bot.keyboards.menu import main_menu_keyboard
from bot.texts.i18n import DEFAULT_LANGUAGE, text

router = Router()


async def send_main_menu(message: Message) -> None:
    await message.answer(
        format_menu_message("📋", text("main_menu", DEFAULT_LANGUAGE)),
        reply_markup=main_menu_keyboard(DEFAULT_LANGUAGE),
        parse_mode=MENU_PARSE_MODE,
    )


@router.callback_query(F.data == "menu:open")
async def open_menu_callback(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.answer(
            format_menu_message("📋", text("main_menu", DEFAULT_LANGUAGE)),
            reply_markup=main_menu_keyboard(DEFAULT_LANGUAGE),
            parse_mode=MENU_PARSE_MODE,
        )
    await callback.answer()
