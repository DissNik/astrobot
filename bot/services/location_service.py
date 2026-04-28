from datetime import datetime

from bot.domain.enums import LocationSource, SkyPreset
from bot.domain.models import Location


def build_location_from_coordinates(
    user_id: int,
    name: str,
    latitude: float,
    longitude: float,
    sky_preset: SkyPreset | str,
    bortle_class: int | None,
    enabled_for_subscription: bool,
    created_at: datetime,
    source: LocationSource | str = LocationSource.COORDINATES,
) -> Location:
    name = name.strip()
    if not name:
        raise ValueError("name must not be empty")
    sky_preset = _normalize_sky_preset(sky_preset)
    source = _normalize_location_source(source)

    if not -90 <= latitude <= 90:
        raise ValueError("latitude must be between -90 and 90")
    if not -180 <= longitude <= 180:
        raise ValueError("longitude must be between -180 and 180")
    if bortle_class is not None and not 1 <= bortle_class <= 9:
        raise ValueError("bortle_class must be between 1 and 9")
    if sky_preset is SkyPreset.CUSTOM_BORTLE and bortle_class is None:
        raise ValueError("custom bortle sky preset requires bortle_class")

    return Location(
        id=None,
        user_id=user_id,
        name=name,
        latitude=latitude,
        longitude=longitude,
        source=source,
        sky_preset=sky_preset,
        bortle_class=bortle_class,
        enabled_for_subscription=enabled_for_subscription,
        created_at=created_at,
    )


def _normalize_sky_preset(sky_preset: SkyPreset | str) -> SkyPreset:
    try:
        return SkyPreset(sky_preset)
    except ValueError as error:
        raise ValueError("sky_preset must be a valid SkyPreset") from error


def _normalize_location_source(source: LocationSource | str) -> LocationSource:
    try:
        return LocationSource(source)
    except ValueError as error:
        raise ValueError("source must be a valid LocationSource") from error
