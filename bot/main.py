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
from bot.scheduler.jobs import due_subscriptions, send_due_subscriptions
from bot.scheduler.runner import create_scheduler, schedule_subscription_job
from bot.services.forecast_service import build_location_forecast, provider_days_for_nights


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
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
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
    dispatcher["owner_telegram_ids"] = settings.owner_telegram_ids
    dispatcher["stats"] = repositories.stats
    dispatcher["users"] = repositories.users
    dispatcher["locations"] = repositories.locations
    dispatcher["subscriptions"] = repositories.subscriptions
    dispatcher["connection"] = connection
    dispatcher["geocoding"] = providers.geocoding
    dispatcher["weather"] = providers.weather

    for router in _routers():
        dispatcher.include_router(router)

    scheduler = create_scheduler()
    schedule_subscription_job(
        scheduler,
        lambda: _dispatch_due_subscriptions(bot, repositories, providers.weather),
    )

    return AppContext(
        settings=settings,
        bot=bot,
        dispatcher=dispatcher,
        connection=connection,
        http=http,
        repositories=repositories,
        providers=providers,
        scheduler=scheduler,
    )


async def run() -> None:
    settings = Settings()
    logging.basicConfig(level=settings.log_level)
    context = create_app_context(settings)

    try:
        context.scheduler.start()
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


async def _dispatch_due_subscriptions(
    bot: Bot,
    repositories: Repositories,
    weather: OpenMeteoClient,
) -> None:
    subscriptions = due_subscriptions(
        repositories.subscriptions.list_enabled(),
        load_user=repositories.users.get,
    )
    await send_due_subscriptions(
        subscriptions,
        load_reports=lambda subscription: _load_subscription_reports(
            subscription,
            repositories,
            weather,
        ),
        load_user=repositories.users.get,
        send_message=bot.send_message,
    )


async def _load_subscription_reports(
    subscription,
    repositories: Repositories,
    weather: OpenMeteoClient,
):
    reports = []
    for location in repositories.locations.list_for_user(subscription.user_id):
        if not location.enabled_for_subscription:
            continue

        provider_forecast = await weather.forecast(
            latitude=location.latitude,
            longitude=location.longitude,
            days=provider_days_for_nights(subscription.forecast_days),
        )
        reports.append(
            build_location_forecast(location, provider_forecast, subscription.observing_profile)
        )
    return reports


if __name__ == "__main__":
    main()
