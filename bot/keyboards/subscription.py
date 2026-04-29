from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.texts.i18n import normalize_language, text


def subscription_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    language = normalize_language(language)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=text("enable_alerts", language), callback_data="subscription:enable"
                )
            ],
            [
                InlineKeyboardButton(
                    text=text("disable_alerts", language), callback_data="subscription:disable"
                )
            ],
        ]
    )
