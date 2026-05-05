import sqlite3
from datetime import UTC, datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.domain.enums import LocationSource, SkyPreset
from bot.handlers.common import (
    edit_callback_message,
    language_for_message,
    language_for_user,
    message_user_id,
)
from bot.keyboards.locations import (
    location_manage_keyboard,
    locations_list_keyboard,
)
from bot.keyboards.menu import main_menu_keyboard
from bot.providers.geocoding import GeocodingClient
from bot.repositories.locations import LocationRepository
from bot.repositories.users import UserRepository
from bot.services.location_service import build_location_from_coordinates
from bot.services.user_service import ensure_user
from bot.texts.i18n import DEFAULT_LANGUAGE, normalize_language, text
from bot.texts.message_format import MENU_PARSE_MODE, format_menu_message

router = Router()


class AddLocationStates(StatesGroup):
    waiting_for_location_input = State()
    waiting_for_name = State()
    waiting_for_rename = State()


@router.message(Command("locations"))
@router.message(F.text == "📍 Локации")
@router.message(F.text == "📍 Locations")
async def locations_command(
    message: Message,
    locations: LocationRepository,
    users: UserRepository | None = None,
) -> None:
    language = language_for_message(message, users)
    user_id = message_user_id(message)
    saved_locations = locations.list_for_user(user_id) if user_id is not None else []
    await message.answer(
        _format_locations(saved_locations, language),
        reply_markup=locations_list_keyboard(saved_locations, language),
        parse_mode=MENU_PARSE_MODE,
    )


@router.callback_query(F.data == "locations:open")
async def locations_callback(
    callback: CallbackQuery,
    locations: LocationRepository,
    users: UserRepository | None = None,
) -> None:
    language = language_for_user(callback.from_user.id, users)
    saved_locations = locations.list_for_user(callback.from_user.id)
    if callback.message:
        await edit_callback_message(
            callback.message,
            _format_locations(saved_locations, language),
            reply_markup=locations_list_keyboard(saved_locations, language),
            parse_mode=MENU_PARSE_MODE,
        )
    await callback.answer()


@router.callback_query(F.data == "locations:add")
async def locations_add_callback(
    callback: CallbackQuery,
    state: FSMContext,
    users: UserRepository | None = None,
) -> None:
    await state.set_state(AddLocationStates.waiting_for_location_input)
    language = language_for_user(callback.from_user.id, users)
    if callback.message:
        await callback.message.answer(text("add_location_prompt", language))
    await callback.answer()


@router.message(AddLocationStates.waiting_for_location_input)
async def add_location_input_message(
    message: Message,
    state: FSMContext,
    users: UserRepository,
    locations: LocationRepository,
    connection: sqlite3.Connection,
    geocoding: GeocodingClient,
) -> None:
    user_id = message_user_id(message)
    language = language_for_user(user_id, users)
    resolved_location = await _resolve_location_input(message, geocoding)
    if user_id is None or resolved_location is None:
        await message.answer(text("invalid_location_input", language))
        return

    latitude, longitude, source, default_name = resolved_location
    await state.update_data(
        latitude=latitude,
        longitude=longitude,
        source=source.value,
        default_name=default_name,
    )
    await state.set_state(AddLocationStates.waiting_for_name)
    await message.answer(text("location_name_prompt", language))


add_location_coordinates_message = add_location_input_message


@router.message(AddLocationStates.waiting_for_name)
async def add_location_name_message(
    message: Message,
    state: FSMContext,
    users: UserRepository,
    locations: LocationRepository,
    connection: sqlite3.Connection,
) -> None:
    user_id = message_user_id(message)
    language = language_for_user(user_id, users)
    data = await state.get_data()
    name = _normalize_location_name(message.text, data.get("default_name"))
    if user_id is None or not name:
        await message.answer(text("invalid_location_name", language))
        return

    now = datetime.now(tz=UTC)
    user = ensure_user(user_id, users, now)
    language = normalize_language(user.language)
    location = locations.add(
        build_location_from_coordinates(
            user_id=user_id,
            name=name,
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            sky_preset=SkyPreset.SUBURB,
            bortle_class=None,
            enabled_for_subscription=True,
            created_at=now,
            source=LocationSource(data["source"]),
        )
    )
    connection.commit()
    await state.clear()
    await message.answer(
        text("location_saved", language).format(name=location.name),
        reply_markup=main_menu_keyboard(language),
    )


@router.callback_query(F.data == "locations:list")
async def locations_list_callback(
    callback: CallbackQuery,
    locations: LocationRepository,
    users: UserRepository | None = None,
) -> None:
    user_id = callback.from_user.id
    language = language_for_user(user_id, users)
    saved_locations = locations.list_for_user(user_id)
    if callback.message:
        await edit_callback_message(
            callback.message,
            _format_locations(saved_locations, language),
            reply_markup=locations_list_keyboard(saved_locations, language),
            parse_mode=MENU_PARSE_MODE,
        )
    await callback.answer()


@router.callback_query(F.data.startswith("locations:manage:"))
async def location_manage_callback(
    callback: CallbackQuery,
    locations: LocationRepository,
    users: UserRepository | None = None,
) -> None:
    language = language_for_user(callback.from_user.id, users)
    location_id = _parse_location_callback_id(callback.data, "locations:manage:")
    location = _find_location_for_callback(callback, locations, location_id)
    if location is None:
        await callback.answer(text("location_not_found_short", language), show_alert=True)
        return

    if callback.message:
        await edit_callback_message(
            callback.message,
            _format_location_details(location, language),
            reply_markup=location_manage_keyboard(location, language),
            parse_mode=MENU_PARSE_MODE,
        )
    await callback.answer()


@router.callback_query(F.data.startswith("locations:rename:"))
async def rename_location_callback(
    callback: CallbackQuery,
    state: FSMContext,
    locations: LocationRepository,
    users: UserRepository | None = None,
) -> None:
    language = language_for_user(callback.from_user.id, users)
    location_id = _parse_location_callback_id(callback.data, "locations:rename:")
    location = _find_location_for_callback(callback, locations, location_id)
    if location is None or location.id is None:
        await callback.answer(text("location_not_found_short", language), show_alert=True)
        return

    await state.update_data(rename_location_id=location.id)
    await state.set_state(AddLocationStates.waiting_for_rename)
    if callback.message:
        await callback.message.answer(text("rename_location_prompt", language))
    await callback.answer()


@router.message(AddLocationStates.waiting_for_rename)
async def rename_location_message(
    message: Message,
    state: FSMContext,
    locations: LocationRepository,
    connection: sqlite3.Connection,
    users: UserRepository | None = None,
) -> None:
    user_id = message_user_id(message)
    language = language_for_user(user_id, users)
    data = await state.get_data()
    location_id = data.get("rename_location_id")
    name = _normalize_location_name(message.text, None)
    if user_id is None or location_id is None or not name:
        await message.answer(text("invalid_location_name", language))
        return

    locations.rename_for_user(int(location_id), user_id, name)
    connection.commit()
    await state.clear()
    await message.answer(
        text("location_renamed", language).format(name=name),
        reply_markup=main_menu_keyboard(language),
    )


@router.callback_query(F.data.startswith("locations:delete:"))
async def delete_location_callback(
    callback: CallbackQuery,
    locations: LocationRepository,
    connection: sqlite3.Connection,
    users: UserRepository | None = None,
) -> None:
    language = language_for_user(callback.from_user.id, users)
    location_id = _parse_location_callback_id(callback.data, "locations:delete:")
    if location_id is None:
        await callback.answer(text("location_not_found_short", language), show_alert=True)
        return

    locations.delete_for_user(location_id, callback.from_user.id)
    connection.commit()
    if callback.message:
        saved_locations = locations.list_for_user(callback.from_user.id)
        await edit_callback_message(
            callback.message,
            _format_locations(saved_locations, language),
            reply_markup=locations_list_keyboard(saved_locations, language),
            parse_mode=MENU_PARSE_MODE,
        )
    await callback.answer()


@router.callback_query(F.data.startswith("locations:toggle_subscription:"))
async def toggle_location_subscription_callback(
    callback: CallbackQuery,
    locations: LocationRepository,
    connection: sqlite3.Connection,
    users: UserRepository | None = None,
) -> None:
    language = language_for_user(callback.from_user.id, users)
    location_id = _parse_location_callback_id(callback.data, "locations:toggle_subscription:")
    location = _find_location_for_callback(callback, locations, location_id)
    if location is None or location.id is None:
        await callback.answer(text("location_not_found_short", language), show_alert=True)
        return

    enabled = not location.enabled_for_subscription
    locations.set_subscription_enabled_for_user(location.id, callback.from_user.id, enabled)
    connection.commit()
    if callback.message:
        updated_location = locations.get_for_user(location.id, callback.from_user.id)
        if updated_location is not None:
            await edit_callback_message(
                callback.message,
                _format_location_details(updated_location, language),
                reply_markup=location_manage_keyboard(updated_location, language),
                parse_mode=MENU_PARSE_MODE,
            )
    await callback.answer()


def _parse_coordinates(text: str | None) -> tuple[float, float] | None:
    if text is None:
        return None

    parts = text.replace(",", " ").split()
    if len(parts) != 2:
        return None

    try:
        latitude = float(parts[0])
        longitude = float(parts[1])
    except ValueError:
        return None

    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        return None

    return latitude, longitude


def _default_location_name(latitude: float, longitude: float) -> str:
    return text("location_default_name", DEFAULT_LANGUAGE).format(
        latitude=latitude,
        longitude=longitude,
    )


def _format_locations(locations: list, language: str = DEFAULT_LANGUAGE) -> str:
    if not locations:
        return format_menu_message("📍", text("no_saved_locations", language))

    return format_menu_message("📍", text("your_locations", language))


async def _resolve_location_input(
    message: Message,
    geocoding: GeocodingClient,
) -> tuple[float, float, LocationSource, str] | None:
    telegram_location = getattr(message, "location", None)
    if telegram_location is not None:
        latitude = float(telegram_location.latitude)
        longitude = float(telegram_location.longitude)
        return (
            latitude,
            longitude,
            LocationSource.TELEGRAM_GEO,
            _default_location_name(latitude, longitude),
        )

    coordinates = _parse_coordinates(message.text)
    if coordinates is not None:
        latitude, longitude = coordinates
        return (
            latitude,
            longitude,
            LocationSource.COORDINATES,
            _default_location_name(latitude, longitude),
        )

    query = (message.text or "").strip()
    if not query:
        return None

    candidates = await geocoding.search(query, count=1)
    if not candidates:
        return None

    candidate = candidates[0]
    name = candidate.name
    if candidate.country:
        name = f"{candidate.name}, {candidate.country}"
    return candidate.latitude, candidate.longitude, LocationSource.CITY, name


def _normalize_location_name(text: str | None, default_name: str | None) -> str | None:
    value = (text or "").strip()
    if value == "-" and default_name:
        return default_name
    if not value:
        return None
    return value


def _parse_location_callback_id(data: str | None, prefix: str) -> int | None:
    if data is None or not data.startswith(prefix):
        return None
    try:
        return int(data.removeprefix(prefix))
    except ValueError:
        return None


def _find_location_for_callback(
    callback: CallbackQuery,
    locations: LocationRepository,
    location_id: int | None,
):
    if location_id is None:
        return None
    return locations.get_for_user(location_id, callback.from_user.id)


def _format_location_details(location, language: str = DEFAULT_LANGUAGE) -> str:  # noqa: ANN001
    subscription = text("enabled" if location.enabled_for_subscription else "disabled", language)
    body = (
        f"{text('coordinates', language)}: {location.latitude:.4f}, {location.longitude:.4f}\n"
        f"{text('source', language)}: {_format_source(location.source, language)}\n"
        f"{text('alerts', language)}: {subscription}"
    )
    return format_menu_message("📍", location.name, body)


def _format_source(source: LocationSource, language: str = DEFAULT_LANGUAGE) -> str:
    return {
        LocationSource.CITY: text("source_city", language),
        LocationSource.COORDINATES: text("source_coordinates", language),
        LocationSource.TELEGRAM_GEO: text("source_telegram_geo", language),
    }[source]
