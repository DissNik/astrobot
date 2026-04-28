from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔭 Прогноз"),
                KeyboardButton(text="📍 Локации"),
            ],
            [
                KeyboardButton(text="📬 Рассылка"),
                KeyboardButton(text="⚙️ Настройки"),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
