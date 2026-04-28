from typing import Any

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


def is_owner(user_id: int | None, owner_ids: tuple[int, ...]) -> bool:
    return user_id in owner_ids


async def _resolve_stats_text(stats: Any | None) -> str:
    if hasattr(stats, "summary"):
        summary = stats.summary()
        if hasattr(summary, "__await__"):
            summary = await summary
        return _format_stats_summary(summary)

    return _format_stats_summary(stats)


def _format_stats_summary(summary: Any) -> str:
    if not isinstance(summary, dict):
        return str(summary)

    return "\n".join(
        [
            "Статистика бота:",
            f"Пользователи: {summary.get('users', 0)}",
            f"Локации: {summary.get('locations', 0)}",
            f"Активные подписки: {summary.get('active_subscriptions', 0)}",
        ]
    )


@router.message(Command("stats"))
async def stats_command(
    message: Message,
    owner_telegram_ids: tuple[int, ...],
    stats: Any,
) -> None:
    user_id = message.from_user.id if message.from_user else None
    if not is_owner(user_id=user_id, owner_ids=owner_telegram_ids):
        await message.answer("Команда доступна только владельцу бота.")
        return

    await message.answer(await _resolve_stats_text(stats))
