from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.domain.enums import ObservingProfile
from bot.keyboards.forecast import forecast_locations_keyboard
from bot.keyboards.menu import main_menu_keyboard
from bot.providers.open_meteo import OpenMeteoClient
from bot.repositories.locations import LocationRepository
from bot.repositories.users import UserRepository
from bot.services.forecast_service import build_location_forecast, provider_days_for_nights
from bot.services.report_formatter import FORECAST_PARSE_MODE, format_forecast_report

router = Router()

FORECAST_TEXT = "Прогноз. Выберите локацию наблюдения, чтобы получить астрономический прогноз."
SELECT_LOCATION_TEXT = "Выберите локацию наблюдения для прогноза."
NO_LOCATIONS_TEXT = "Сначала добавьте локацию наблюдения в разделе «Локации»."
LOCATION_NOT_FOUND_TEXT = "Не нашел эту локацию наблюдения. Откройте прогноз заново."
FORECAST_ERROR_TEXT = "Не удалось получить прогноз. Попробуйте позже."


@router.message(Command("forecast"))
@router.message(F.text == "🔭 Прогноз")
async def forecast_command(message: Message, locations: LocationRepository) -> None:
    user_id = _message_user_id(message)
    if user_id is None:
        await message.answer(NO_LOCATIONS_TEXT)
        return
    await _send_forecast_locations(message, user_id, locations)


@router.callback_query(F.data == "forecast:open")
async def forecast_callback(callback: CallbackQuery, locations: LocationRepository) -> None:
    if callback.message:
        await _send_forecast_locations(callback.message, callback.from_user.id, locations)
    await callback.answer()


@router.callback_query(F.data.startswith("forecast:location:"))
async def forecast_location_callback(
    callback: CallbackQuery,
    users: UserRepository,
    locations: LocationRepository,
    weather: OpenMeteoClient,
) -> None:
    location_id = _parse_location_id(callback.data)
    location = _find_user_location(locations, callback.from_user.id, location_id)
    if location is None:
        await callback.answer(LOCATION_NOT_FOUND_TEXT, show_alert=True)
        return

    user = users.get(callback.from_user.id)
    profile = user.observing_profile if user is not None else ObservingProfile.DEEP_SKY
    forecast_days = user.forecast_days if user is not None else 3

    try:
        provider_forecast = await weather.forecast(
            latitude=location.latitude,
            longitude=location.longitude,
            days=provider_days_for_nights(forecast_days),
        )
    except Exception:
        await callback.answer(FORECAST_ERROR_TEXT, show_alert=True)
        return

    report = build_location_forecast(location, provider_forecast, profile)
    if callback.message:
        await callback.message.answer(
            format_forecast_report([report]),
            parse_mode=FORECAST_PARSE_MODE,
            reply_markup=main_menu_keyboard(),
        )
    await callback.answer()


async def _send_forecast_locations(
    message: Message,
    user_id: int,
    locations: LocationRepository,
) -> None:
    saved_locations = locations.list_for_user(user_id)
    if not saved_locations:
        await message.answer(NO_LOCATIONS_TEXT)
        return

    await message.answer(
        SELECT_LOCATION_TEXT,
        reply_markup=forecast_locations_keyboard(saved_locations),
    )


def _parse_location_id(data: str | None) -> int | None:
    if data is None:
        return None
    try:
        return int(data.removeprefix("forecast:location:"))
    except ValueError:
        return None


def _find_user_location(
    locations: LocationRepository,
    user_id: int,
    location_id: int | None,
):
    if location_id is None:
        return None

    for location in locations.list_for_user(user_id):
        if location.id == location_id:
            return location
    return None


def _message_user_id(message: Message) -> int | None:
    if message.from_user is None:
        return None
    return message.from_user.id
