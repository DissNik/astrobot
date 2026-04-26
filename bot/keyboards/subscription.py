from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def subscription_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Включить рассылку", callback_data="subscription:enable")],
            [InlineKeyboardButton(text="Отключить рассылку", callback_data="subscription:disable")],
            [InlineKeyboardButton(text="Назад", callback_data="menu:open")],
        ]
    )
