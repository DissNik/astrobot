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
from bot.texts.i18n import DEFAULT_LANGUAGE, normalize_language, text
from bot.texts.message_format import MENU_PARSE_MODE, format_menu_message

router = Router()

@router.message(Command("forecast"))
@router.message(F.text == "🔭 Прогноз")
@router.message(F.text == "🔭 Forecast")
async def forecast_command(
    message: Message,
    locations: LocationRepository,
    users: UserRepository,
) -> None:
    user_id = _message_user_id(message)
    language = _language_for_user(user_id, users)
    if user_id is None:
        await message.answer(text("add_location_first", language))
        return
    await _send_forecast_locations(message, user_id, locations, language)


@router.callback_query(F.data == "forecast:open")
async def forecast_callback(
    callback: CallbackQuery,
    locations: LocationRepository,
    users: UserRepository,
) -> None:
    language = _language_for_user(callback.from_user.id, users)
    if callback.message:
        await _send_forecast_locations(callback.message, callback.from_user.id, locations, language)
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
        await callback.answer(text("location_not_found", DEFAULT_LANGUAGE), show_alert=True)
        return

    user = users.get(callback.from_user.id)
    language = normalize_language(user.language if user is not None else None)
    profile = user.observing_profile if user is not None else ObservingProfile.DEEP_SKY
    forecast_days = user.forecast_days if user is not None else 3

    try:
        provider_forecast = await weather.forecast(
            latitude=location.latitude,
            longitude=location.longitude,
            days=provider_days_for_nights(forecast_days),
        )
    except Exception:
        await callback.answer(text("forecast_error", language), show_alert=True)
        return

    report = build_location_forecast(location, provider_forecast, profile)
    if callback.message:
        await callback.message.answer(
            format_forecast_report([report], language=language),
            parse_mode=FORECAST_PARSE_MODE,
            reply_markup=main_menu_keyboard(language),
        )
    await callback.answer()


async def _send_forecast_locations(
    message: Message,
    user_id: int,
    locations: LocationRepository,
    language: str,
) -> None:
    saved_locations = locations.list_for_user(user_id)
    if not saved_locations:
        await message.answer(text("add_location_first", language))
        return

    await message.answer(
        format_menu_message("🔭", text("choose_location", language)),
        reply_markup=forecast_locations_keyboard(saved_locations),
        parse_mode=MENU_PARSE_MODE,
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


def _language_for_user(user_id: int | None, users: UserRepository) -> str:
    if user_id is None:
        return DEFAULT_LANGUAGE
    user = users.get(user_id)
    if user is None:
        return DEFAULT_LANGUAGE
    return normalize_language(user.language)
