from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.domain.models import Location


def forecast_locations_keyboard(locations: list[Location]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=location.name, callback_data=f"forecast:location:{location.id}")]
        for location in locations
        if location.id is not None
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
