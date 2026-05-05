from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message

from bot.texts.i18n import text

MAIN_MENU_TEXTS = {
    text("menu_forecast", "en"),
    text("menu_locations", "en"),
    text("menu_subscription", "en"),
    text("menu_settings", "en"),
    text("menu_forecast", "ru"),
    text("menu_locations", "ru"),
    text("menu_subscription", "ru"),
    text("menu_settings", "ru"),
}

MAIN_MENU_COMMANDS = {
    "/start",
    "/forecast",
    "/locations",
    "/subscribe",
    "/settings",
}


class MainMenuStateResetMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        state = data.get("state")
        if (
            hasattr(state, "get_state")
            and hasattr(state, "clear")
            and await state.get_state()
            and _is_main_menu_text(event.text)
        ):
            await state.clear()

        return await handler(event, data)


def _is_main_menu_text(value: str | None) -> bool:
    if value is None:
        return False

    stripped = value.strip()
    if stripped in MAIN_MENU_TEXTS:
        return True

    command = stripped.split(maxsplit=1)[0].split("@", maxsplit=1)[0]
    return command in MAIN_MENU_COMMANDS
