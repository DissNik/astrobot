from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.domain.models import Location


def locations_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Добавить локацию", callback_data="locations:add")],
            [InlineKeyboardButton(text="Мои локации", callback_data="locations:list")],
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
        "Выключить из рассылки"
        if location.enabled_for_subscription
        else "Включить в рассылку"
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Переименовать",
                    callback_data=f"locations:rename:{location.id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=subscription_text,
                    callback_data=f"locations:toggle_subscription:{location.id}",
                )
            ],
            [InlineKeyboardButton(text="Удалить", callback_data=f"locations:delete:{location.id}")],
            [InlineKeyboardButton(text="К списку", callback_data="locations:list")],
        ]
    )
