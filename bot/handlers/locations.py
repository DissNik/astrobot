import sqlite3
from datetime import UTC, datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.domain.enums import LocationSource, ObservingProfile, SkyPreset
from bot.domain.models import User
from bot.keyboards.locations import (
    location_manage_keyboard,
    locations_keyboard,
    locations_list_keyboard,
)
from bot.keyboards.menu import main_menu_keyboard
from bot.providers.geocoding import GeocodingClient
from bot.repositories.locations import LocationRepository
from bot.repositories.users import UserRepository
from bot.services.location_service import build_location_from_coordinates

router = Router()

LOCATIONS_TEXT = "Локации наблюдения. Здесь можно управлять сохраненными местами."
ADD_LOCATION_PROMPT = (
    "Отправьте город, координаты в формате 45.0448, 38.976 или геолокацию Telegram."
)
INVALID_COORDINATES_TEXT = (
    "Не смог найти локацию. Отправьте город, координаты или геолокацию Telegram."
)
LOCATION_NAME_PROMPT = "Введите название локации."
INVALID_LOCATION_NAME_TEXT = "Название локации не должно быть пустым."
LOCATION_NOT_FOUND_TEXT = "Не нашел эту локацию. Откройте список локаций заново."
RENAME_LOCATION_PROMPT = "Введите новое название локации."


class AddLocationStates(StatesGroup):
    waiting_for_location_input = State()
    waiting_for_name = State()
    waiting_for_rename = State()


@router.message(Command("locations"))
@router.message(F.text == "📍 Локации")
async def locations_command(message: Message) -> None:
    await message.answer(LOCATIONS_TEXT, reply_markup=locations_keyboard())


@router.callback_query(F.data == "locations:open")
async def locations_callback(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.answer(LOCATIONS_TEXT, reply_markup=locations_keyboard())
    await callback.answer()


@router.callback_query(F.data == "locations:add")
async def locations_add_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddLocationStates.waiting_for_location_input)
    if callback.message:
        await callback.message.answer(ADD_LOCATION_PROMPT)
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
    user_id = _message_user_id(message)
    resolved_location = await _resolve_location_input(message, geocoding)
    if user_id is None or resolved_location is None:
        await message.answer(INVALID_COORDINATES_TEXT)
        return

    latitude, longitude, source, default_name = resolved_location
    await state.update_data(
        latitude=latitude,
        longitude=longitude,
        source=source.value,
        default_name=default_name,
    )
    await state.set_state(AddLocationStates.waiting_for_name)
    await message.answer(LOCATION_NAME_PROMPT)


add_location_coordinates_message = add_location_input_message


@router.message(AddLocationStates.waiting_for_name)
async def add_location_name_message(
    message: Message,
    state: FSMContext,
    users: UserRepository,
    locations: LocationRepository,
    connection: sqlite3.Connection,
) -> None:
    user_id = _message_user_id(message)
    data = await state.get_data()
    name = _normalize_location_name(message.text, data.get("default_name"))
    if user_id is None or not name:
        await message.answer(INVALID_LOCATION_NAME_TEXT)
        return

    now = datetime.now(tz=UTC)
    users.upsert(
        User(
            telegram_id=user_id,
            timezone="UTC",
            language="ru",
            forecast_days=3,
            observing_profile=ObservingProfile.DEEP_SKY,
            score_threshold=60,
            created_at=now,
        )
    )
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
    await message.answer(f"Локация сохранена: {location.name}", reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "locations:list")
async def locations_list_callback(callback: CallbackQuery, locations: LocationRepository) -> None:
    user_id = callback.from_user.id
    saved_locations = locations.list_for_user(user_id)
    if callback.message:
        await callback.message.answer(
            _format_locations(saved_locations),
            reply_markup=locations_list_keyboard(saved_locations),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("locations:manage:"))
async def location_manage_callback(callback: CallbackQuery, locations: LocationRepository) -> None:
    location_id = _parse_location_callback_id(callback.data, "locations:manage:")
    location = _find_location_for_callback(callback, locations, location_id)
    if location is None:
        await callback.answer(LOCATION_NOT_FOUND_TEXT, show_alert=True)
        return

    if callback.message:
        await callback.message.answer(
            _format_location_details(location),
            reply_markup=location_manage_keyboard(location),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("locations:rename:"))
async def rename_location_callback(
    callback: CallbackQuery,
    state: FSMContext,
    locations: LocationRepository,
) -> None:
    location_id = _parse_location_callback_id(callback.data, "locations:rename:")
    location = _find_location_for_callback(callback, locations, location_id)
    if location is None or location.id is None:
        await callback.answer(LOCATION_NOT_FOUND_TEXT, show_alert=True)
        return

    await state.update_data(rename_location_id=location.id)
    await state.set_state(AddLocationStates.waiting_for_rename)
    if callback.message:
        await callback.message.answer(RENAME_LOCATION_PROMPT)
    await callback.answer()


@router.message(AddLocationStates.waiting_for_rename)
async def rename_location_message(
    message: Message,
    state: FSMContext,
    locations: LocationRepository,
    connection: sqlite3.Connection,
) -> None:
    user_id = _message_user_id(message)
    data = await state.get_data()
    location_id = data.get("rename_location_id")
    name = _normalize_location_name(message.text, None)
    if user_id is None or location_id is None or not name:
        await message.answer(INVALID_LOCATION_NAME_TEXT)
        return

    locations.rename_for_user(int(location_id), user_id, name)
    connection.commit()
    await state.clear()
    await message.answer(f"Локация переименована: {name}", reply_markup=main_menu_keyboard())


@router.callback_query(F.data.startswith("locations:delete:"))
async def delete_location_callback(
    callback: CallbackQuery,
    locations: LocationRepository,
    connection: sqlite3.Connection,
) -> None:
    location_id = _parse_location_callback_id(callback.data, "locations:delete:")
    if location_id is None:
        await callback.answer(LOCATION_NOT_FOUND_TEXT, show_alert=True)
        return

    locations.delete_for_user(location_id, callback.from_user.id)
    connection.commit()
    if callback.message:
        await callback.message.answer("Локация удалена.", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("locations:toggle_subscription:"))
async def toggle_location_subscription_callback(
    callback: CallbackQuery,
    locations: LocationRepository,
    connection: sqlite3.Connection,
) -> None:
    location_id = _parse_location_callback_id(callback.data, "locations:toggle_subscription:")
    location = _find_location_for_callback(callback, locations, location_id)
    if location is None or location.id is None:
        await callback.answer(LOCATION_NOT_FOUND_TEXT, show_alert=True)
        return

    enabled = not location.enabled_for_subscription
    locations.set_subscription_enabled_for_user(location.id, callback.from_user.id, enabled)
    connection.commit()
    text = "Локация включена в рассылку." if enabled else "Локация выключена из рассылки."
    if callback.message:
        await callback.message.answer(text, reply_markup=main_menu_keyboard())
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
    return f"Локация {latitude:.4f}, {longitude:.4f}"


def _format_locations(locations: list) -> str:
    if not locations:
        return "У вас пока нет сохраненных локаций."

    lines = ["Ваши локации:"]
    for index, location in enumerate(locations, start=1):
        lines.append(
            f"{index}. {location.name} — {location.latitude:.4f}, {location.longitude:.4f}"
        )
    return "\n".join(lines)


def _message_user_id(message: Message) -> int | None:
    if message.from_user is None:
        return None
    return message.from_user.id


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


def _format_location_details(location) -> str:  # noqa: ANN001
    subscription = "включена" if location.enabled_for_subscription else "выключена"
    return (
        f"{location.name}\n"
        f"Координаты: {location.latitude:.4f}, {location.longitude:.4f}\n"
        f"Источник: {_format_source(location.source)}\n"
        f"Рассылка: {subscription}"
    )


def _format_source(source: LocationSource) -> str:
    return {
        LocationSource.CITY: "город",
        LocationSource.COORDINATES: "координаты",
        LocationSource.TELEGRAM_GEO: "геолокация Telegram",
    }[source]
