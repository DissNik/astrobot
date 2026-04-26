from typing import Any

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


def is_owner(user_id: int | None, owner_id: int) -> bool:
    return user_id == owner_id


async def _resolve_stats_text(stats: Any | None) -> str:
    if stats is None:
        return "Статистика пока недоступна."

    if hasattr(stats, "summary"):
        summary = stats.summary()
        if hasattr(summary, "__await__"):
            summary = await summary
        return str(summary)

    return str(stats)


@router.message(Command("stats"))
async def stats_command(
    message: Message,
    owner_id: int,
    stats: Any | None = None,
) -> None:
    user_id = message.from_user.id if message.from_user else None
    if not is_owner(user_id=user_id, owner_id=owner_id):
        await message.answer("Команда доступна только владельцу бота.")
        return

    await message.answer(await _resolve_stats_text(stats))
