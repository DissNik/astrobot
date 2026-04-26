import asyncio
import logging
import sqlite3
from dataclasses import dataclass

import httpx
from aiogram import Bot, Dispatcher, Router
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.config import Settings
from bot.db.connection import connect
from bot.db.migrations import migrate
from bot.handlers import admin, forecast, locations, menu, start
from bot.handlers import settings as settings_handler
from bot.handlers import subscription as subscription_handler
from bot.providers.geocoding import GeocodingClient
from bot.providers.open_meteo import OpenMeteoClient
from bot.repositories.forecast_cache import ForecastCacheRepository
from bot.repositories.locations import LocationRepository
from bot.repositories.stats import StatsRepository
from bot.repositories.subscriptions import SubscriptionRepository
from bot.repositories.users import UserRepository
from bot.scheduler.runner import create_scheduler


@dataclass(frozen=True)
class Repositories:
    users: UserRepository
    locations: LocationRepository
    subscriptions: SubscriptionRepository
    forecast_cache: ForecastCacheRepository
    stats: StatsRepository


@dataclass(frozen=True)
class Providers:
    geocoding: GeocodingClient
    weather: OpenMeteoClient


@dataclass(frozen=True)
class AppContext:
    settings: Settings
    bot: Bot
    dispatcher: Dispatcher
    connection: sqlite3.Connection
    http: httpx.AsyncClient
    repositories: Repositories
    providers: Providers
    scheduler: AsyncIOScheduler

    async def close(self) -> None:
        await self.http.aclose()
        await self.bot.session.close()
        self.connection.close()


def create_app_context(settings: Settings) -> AppContext:
    connection = connect(settings.database_path)
    migrate(connection)
    connection.commit()

    repositories = Repositories(
        users=UserRepository(connection),
        locations=LocationRepository(connection),
        subscriptions=SubscriptionRepository(connection),
        forecast_cache=ForecastCacheRepository(connection),
        stats=StatsRepository(connection),
    )
    http = httpx.AsyncClient()
    providers = Providers(
        geocoding=GeocodingClient(http),
        weather=OpenMeteoClient(http),
    )
    bot = Bot(settings.telegram_bot_token)
    dispatcher = Dispatcher()
    dispatcher["owner_telegram_id"] = settings.owner_telegram_id
    dispatcher["stats"] = repositories.stats

    for router in _routers():
        dispatcher.include_router(router)

    return AppContext(
        settings=settings,
        bot=bot,
        dispatcher=dispatcher,
        connection=connection,
        http=http,
        repositories=repositories,
        providers=providers,
        scheduler=create_scheduler(),
    )


async def run() -> None:
    settings = Settings()
    logging.basicConfig(level=settings.log_level)
    context = create_app_context(settings)

    try:
        await context.dispatcher.start_polling(context.bot)
    finally:
        await context.close()


def main() -> None:
    asyncio.run(run())


def _routers() -> tuple[Router, ...]:
    return (
        start.router,
        menu.router,
        forecast.router,
        locations.router,
        subscription_handler.router,
        settings_handler.router,
        admin.router,
    )


if __name__ == "__main__":
    main()
