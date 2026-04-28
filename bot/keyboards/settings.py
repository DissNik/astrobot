from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="3 ночи", callback_data="settings:days:3"),
                InlineKeyboardButton(text="5 ночей", callback_data="settings:days:5"),
                InlineKeyboardButton(text="7 ночей", callback_data="settings:days:7"),
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
                    text="Ежедневный дайджест",
                    callback_data="settings:mode:daily_digest",
                ),
                InlineKeyboardButton(
                    text="Только хорошие условия",
                    callback_data="settings:mode:good_conditions_only",
                ),
            ],
            [
                InlineKeyboardButton(text="Порог 50", callback_data="settings:threshold:50"),
                InlineKeyboardButton(text="Порог 60", callback_data="settings:threshold:60"),
                InlineKeyboardButton(text="Порог 70", callback_data="settings:threshold:70"),
                InlineKeyboardButton(text="Порог 80", callback_data="settings:threshold:80"),
            ],
            [InlineKeyboardButton(text="Время рассылки", callback_data="settings:time")],
        ]
    )
