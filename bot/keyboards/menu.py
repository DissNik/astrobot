from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from bot.texts.i18n import normalize_language


def main_menu_keyboard(language: str = "en") -> ReplyKeyboardMarkup:
    language = normalize_language(language)
    if language == "ru":
        forecast = "🔭 Прогноз"
        locations = "📍 Локации"
        subscription = "📬 Рассылка"
        settings = "⚙️ Настройки"
    else:
        forecast = "🔭 Forecast"
        locations = "📍 Locations"
        subscription = "📬 Alerts"
        settings = "⚙️ Settings"

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=forecast),
                KeyboardButton(text=locations),
            ],
            [
                KeyboardButton(text=subscription),
                KeyboardButton(text=settings),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
