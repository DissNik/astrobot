from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message

from bot.repositories.users import UserRepository
from bot.texts.i18n import DEFAULT_LANGUAGE, normalize_language


def message_user_id(message: Message) -> int | None:
    if message.from_user is None:
        return None
    return message.from_user.id


def language_for_user(user_id: int | None, users: UserRepository | None) -> str:
    if user_id is None or users is None:
        return DEFAULT_LANGUAGE
    user = users.get(user_id)
    if user is None:
        return DEFAULT_LANGUAGE
    return normalize_language(user.language)


def language_for_message(message: Message, users: UserRepository | None) -> str:
    return language_for_user(message_user_id(message), users)


async def edit_callback_message(message: Message, text_value: str, reply_markup=None) -> None:  # noqa: ANN001
    try:
        await message.edit_text(text_value, reply_markup=reply_markup)
    except TelegramBadRequest as error:
        if "message is not modified" not in str(error):
            raise
