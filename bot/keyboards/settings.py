from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.texts.i18n import normalize_language, text


def settings_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    language = normalize_language(language)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=text("settings_days_3", language), callback_data="settings:days:3"
                ),
                InlineKeyboardButton(
                    text=text("settings_days_5", language), callback_data="settings:days:5"
                ),
                InlineKeyboardButton(
                    text=text("settings_days_7", language), callback_data="settings:days:7"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=text("settings_language_en", language),
                    callback_data="settings:language:en",
                ),
                InlineKeyboardButton(
                    text=text("settings_language_ru", language),
                    callback_data="settings:language:ru",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=text("settings_profile_deep_sky", language),
                    callback_data="settings:profile:deep_sky",
                ),
                InlineKeyboardButton(
                    text=text("settings_profile_planetary_lunar", language),
                    callback_data="settings:profile:planetary_lunar",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=text("settings_daily_digest", language),
                    callback_data="settings:mode:daily_digest",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=text("settings_good_conditions_only", language),
                    callback_data="settings:mode:good_conditions_only",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=text("settings_threshold_50", language),
                    callback_data="settings:threshold:50",
                ),
                InlineKeyboardButton(
                    text=text("settings_threshold_60", language),
                    callback_data="settings:threshold:60",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=text("settings_threshold_70", language),
                    callback_data="settings:threshold:70",
                ),
                InlineKeyboardButton(
                    text=text("settings_threshold_80", language),
                    callback_data="settings:threshold:80",
                ),
            ],
            [InlineKeyboardButton(text=text("send_time", language), callback_data="settings:time")],
        ]
    )
