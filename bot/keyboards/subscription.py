from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def subscription_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Enable alerts", callback_data="subscription:enable")],
            [InlineKeyboardButton(text="Disable alerts", callback_data="subscription:disable")],
        ]
    )
