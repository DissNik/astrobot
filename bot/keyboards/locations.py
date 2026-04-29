from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.domain.models import Location
from bot.texts.i18n import normalize_language, text


def locations_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    language = normalize_language(language)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=text("add_location", language), callback_data="locations:add"
                )
            ],
            [
                InlineKeyboardButton(
                    text=text("my_locations", language), callback_data="locations:list"
                )
            ],
        ]
    )


def locations_list_keyboard(locations: list[Location]) -> InlineKeyboardMarkup | None:
    rows = [
        [InlineKeyboardButton(text=location.name, callback_data=f"locations:manage:{location.id}")]
        for location in locations
        if location.id is not None
    ]
    if not rows:
        return None

    return InlineKeyboardMarkup(inline_keyboard=rows)


def location_manage_keyboard(location: Location, language: str = "en") -> InlineKeyboardMarkup:
    language = normalize_language(language)
    if location.id is None:
        raise ValueError("location must have id")

    subscription_text = (
        text("disable_alerts", language)
        if location.enabled_for_subscription
        else text("enable_alerts", language)
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=text("rename", language),
                    callback_data=f"locations:rename:{location.id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=subscription_text,
                    callback_data=f"locations:toggle_subscription:{location.id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=text("delete", language), callback_data=f"locations:delete:{location.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text=text("back_to_list", language), callback_data="locations:list"
                )
            ],
        ]
    )
