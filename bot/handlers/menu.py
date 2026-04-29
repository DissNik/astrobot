from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.keyboards.menu import main_menu_keyboard

router = Router()

MENU_TEXT = "Main menu"


async def send_main_menu(message: Message) -> None:
    await message.answer(MENU_TEXT, reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "menu:open")
async def open_menu_callback(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.answer(MENU_TEXT, reply_markup=main_menu_keyboard())
    await callback.answer()
