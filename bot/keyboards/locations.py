from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def locations_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Добавить точку", callback_data="locations:add")],
            [InlineKeyboardButton(text="Мои точки", callback_data="locations:list")],
            [InlineKeyboardButton(text="Назад", callback_data="menu:open")],
        ]
    )
