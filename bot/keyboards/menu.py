from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from bot.texts.i18n import normalize_language, text


def main_menu_keyboard(language: str = "en") -> ReplyKeyboardMarkup:
    language = normalize_language(language)

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=text("menu_forecast", language)),
                KeyboardButton(text=text("menu_locations", language)),
            ],
            [
                KeyboardButton(text=text("menu_subscription", language)),
                KeyboardButton(text=text("menu_settings", language)),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
