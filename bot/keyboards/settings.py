from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.domain.enums import ObservingProfile, SubscriptionMode
from bot.texts.i18n import normalize_language, text


def settings_keyboard(
    language: str = "en",
    selected_language: str | None = None,
    forecast_days: int = 3,
    observing_profile: ObservingProfile = ObservingProfile.DEEP_SKY,
    mode: SubscriptionMode = SubscriptionMode.DAILY_DIGEST,
    score_threshold: int = 60,
) -> InlineKeyboardMarkup:
    language = normalize_language(language)
    selected_language = normalize_language(selected_language or language)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_mark_selected(text("settings_days_3", language), forecast_days == 3),
                    callback_data="settings:days:3",
                ),
                InlineKeyboardButton(
                    text=_mark_selected(text("settings_days_5", language), forecast_days == 5),
                    callback_data="settings:days:5",
                ),
                InlineKeyboardButton(
                    text=_mark_selected(text("settings_days_7", language), forecast_days == 7),
                    callback_data="settings:days:7",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_mark_selected(
                        text("settings_language_en", language), selected_language == "en"
                    ),
                    callback_data="settings:language:en",
                ),
                InlineKeyboardButton(
                    text=_mark_selected(
                        text("settings_language_ru", language), selected_language == "ru"
                    ),
                    callback_data="settings:language:ru",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_mark_selected(
                        text("settings_profile_deep_sky", language),
                        observing_profile is ObservingProfile.DEEP_SKY,
                    ),
                    callback_data="settings:profile:deep_sky",
                ),
                InlineKeyboardButton(
                    text=_mark_selected(
                        text("settings_profile_planetary_lunar", language),
                        observing_profile is ObservingProfile.PLANETARY_LUNAR,
                    ),
                    callback_data="settings:profile:planetary_lunar",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_mark_selected(
                        text("settings_daily_digest", language),
                        mode is SubscriptionMode.DAILY_DIGEST,
                    ),
                    callback_data="settings:mode:daily_digest",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_mark_selected(
                        text("settings_good_conditions_only", language),
                        mode is SubscriptionMode.GOOD_CONDITIONS_ONLY,
                    ),
                    callback_data="settings:mode:good_conditions_only",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_mark_selected(
                        text("settings_threshold_50", language), score_threshold == 50
                    ),
                    callback_data="settings:threshold:50",
                ),
                InlineKeyboardButton(
                    text=_mark_selected(
                        text("settings_threshold_60", language), score_threshold == 60
                    ),
                    callback_data="settings:threshold:60",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_mark_selected(
                        text("settings_threshold_70", language), score_threshold == 70
                    ),
                    callback_data="settings:threshold:70",
                ),
                InlineKeyboardButton(
                    text=_mark_selected(
                        text("settings_threshold_80", language), score_threshold == 80
                    ),
                    callback_data="settings:threshold:80",
                ),
            ],
            [InlineKeyboardButton(text=text("send_time", language), callback_data="settings:time")],
        ]
    )


def _mark_selected(label: str, selected: bool) -> str:
    if selected:
        return f"✅ {label}"
    return label
