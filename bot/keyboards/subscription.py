from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.texts.i18n import normalize_language, text


def subscription_keyboard(language: str = "en", enabled: bool = False) -> InlineKeyboardMarkup:
    language = normalize_language(language)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_mark_selected(text("enabled", language), enabled),
                    callback_data="subscription:enable",
                ),
                InlineKeyboardButton(
                    text=_mark_selected(text("disabled", language), not enabled),
                    callback_data="subscription:disable",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=text("menu_settings", language),
                    callback_data="settings:open",
                )
            ],
        ]
    )


def _mark_selected(label: str, selected: bool) -> str:
    if selected:
        return f"✅ {label}"
    return label
