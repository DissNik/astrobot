from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.domain.models import Location


def locations_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Add location", callback_data="locations:add")],
            [InlineKeyboardButton(text="My locations", callback_data="locations:list")],
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


def location_manage_keyboard(location: Location) -> InlineKeyboardMarkup:
    if location.id is None:
        raise ValueError("location must have id")

    subscription_text = (
        "Disable alerts"
        if location.enabled_for_subscription
        else "Enable alerts"
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Rename",
                    callback_data=f"locations:rename:{location.id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=subscription_text,
                    callback_data=f"locations:toggle_subscription:{location.id}",
                )
            ],
            [InlineKeyboardButton(text="Delete", callback_data=f"locations:delete:{location.id}")],
            [InlineKeyboardButton(text="Back to list", callback_data="locations:list")],
        ]
    )
