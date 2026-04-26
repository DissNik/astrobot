import asyncio
from pathlib import Path

from bot.config import Settings
from bot.main import create_app_context


def test_create_app_context_initializes_dependencies(tmp_path: Path) -> None:
    settings = Settings(
        telegram_bot_token="123:abc",
        owner_telegram_id=42,
        database_path=tmp_path / "astrobot.sqlite3",
    )

    context = create_app_context(settings)

    assert context.bot is not None
    assert context.dispatcher is not None
    assert context.connection is not None
    asyncio.run(context.close())
