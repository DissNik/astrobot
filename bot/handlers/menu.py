from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.keyboards.menu import main_menu_keyboard
from bot.texts.i18n import DEFAULT_LANGUAGE, text

router = Router()


async def send_main_menu(message: Message) -> None:
    await message.answer(
        text("main_menu", DEFAULT_LANGUAGE),
        reply_markup=main_menu_keyboard(DEFAULT_LANGUAGE),
    )


@router.callback_query(F.data == "menu:open")
async def open_menu_callback(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.answer(
            text("main_menu", DEFAULT_LANGUAGE),
            reply_markup=main_menu_keyboard(DEFAULT_LANGUAGE),
        )
    await callback.answer()
