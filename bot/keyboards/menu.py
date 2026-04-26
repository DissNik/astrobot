from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Прогноз", callback_data="forecast:open"),
                InlineKeyboardButton(text="Точки", callback_data="locations:open"),
            ],
            [
                InlineKeyboardButton(text="Рассылка", callback_data="subscription:open"),
                InlineKeyboardButton(text="Настройки", callback_data="settings:open"),
            ],
        ]
    )
