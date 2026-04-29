from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.texts.i18n import normalize_language


def settings_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    language = normalize_language(language)
    if language == "ru":
        days = ("3 ночи", "5 ночей", "7 ночей")
        daily_digest = "Ежедневный дайджест"
        good_only = "Только хорошие условия"
        thresholds = ("Порог 50", "Порог 60", "Порог 70", "Порог 80")
        send_time = "Время рассылки"
    else:
        days = ("3 nights", "5 nights", "7 nights")
        daily_digest = "Daily digest"
        good_only = "Good conditions only"
        thresholds = ("Threshold 50", "Threshold 60", "Threshold 70", "Threshold 80")
        send_time = "Notification time"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=days[0], callback_data="settings:days:3"),
                InlineKeyboardButton(text=days[1], callback_data="settings:days:5"),
                InlineKeyboardButton(text=days[2], callback_data="settings:days:7"),
            ],
            [
                InlineKeyboardButton(text="English", callback_data="settings:language:en"),
                InlineKeyboardButton(text="Русский", callback_data="settings:language:ru"),
            ],
            [
                InlineKeyboardButton(text="Deep-sky", callback_data="settings:profile:deep_sky"),
                InlineKeyboardButton(
                    text="Планеты/Луна",
                    callback_data="settings:profile:planetary_lunar",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=daily_digest,
                    callback_data="settings:mode:daily_digest",
                ),
                InlineKeyboardButton(
                    text=good_only,
                    callback_data="settings:mode:good_conditions_only",
                ),
            ],
            [
                InlineKeyboardButton(text=thresholds[0], callback_data="settings:threshold:50"),
                InlineKeyboardButton(text=thresholds[1], callback_data="settings:threshold:60"),
                InlineKeyboardButton(text=thresholds[2], callback_data="settings:threshold:70"),
                InlineKeyboardButton(text=thresholds[3], callback_data="settings:threshold:80"),
            ],
            [InlineKeyboardButton(text=send_time, callback_data="settings:time")],
        ]
    )
