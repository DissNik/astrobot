from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from bot.domain.enums import LocationSource, SkyPreset
from bot.services.location_service import build_location_from_coordinates


def test_build_location_from_coordinates_validates_bortle() -> None:
    created_at = datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC"))

    location = build_location_from_coordinates(
        user_id=100,
        name="Поле",
        latitude=45.0,
        longitude=39.0,
        sky_preset=SkyPreset.CUSTOM_BORTLE,
        bortle_class=4,
        enabled_for_subscription=True,
        created_at=created_at,
    )

    assert location.name == "Поле"
    assert location.source is LocationSource.COORDINATES
    assert location.bortle_class == 4


@pytest.mark.parametrize("latitude", [-90.1, 90.1])
def test_build_location_from_coordinates_rejects_invalid_latitude(latitude: float) -> None:
    with pytest.raises(ValueError, match="latitude must be between -90 and 90"):
        build_location_from_coordinates(
            user_id=100,
            name="Поле",
            latitude=latitude,
            longitude=39.0,
            sky_preset=SkyPreset.DARK_SITE,
            bortle_class=None,
            enabled_for_subscription=True,
            created_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
        )


@pytest.mark.parametrize("longitude", [-180.1, 180.1])
def test_build_location_from_coordinates_rejects_invalid_longitude(longitude: float) -> None:
    with pytest.raises(ValueError, match="longitude must be between -180 and 180"):
        build_location_from_coordinates(
            user_id=100,
            name="Поле",
            latitude=45.0,
            longitude=longitude,
            sky_preset=SkyPreset.DARK_SITE,
            bortle_class=None,
            enabled_for_subscription=True,
            created_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
        )


@pytest.mark.parametrize("bortle_class", [0, 10])
def test_build_location_from_coordinates_rejects_invalid_bortle_class(
    bortle_class: int,
) -> None:
    with pytest.raises(ValueError, match="bortle_class must be between 1 and 9"):
        build_location_from_coordinates(
            user_id=100,
            name="Поле",
            latitude=45.0,
            longitude=39.0,
            sky_preset=SkyPreset.DARK_SITE,
            bortle_class=bortle_class,
            enabled_for_subscription=True,
            created_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
        )


def test_build_location_from_coordinates_requires_custom_bortle_class() -> None:
    with pytest.raises(ValueError, match="custom bortle sky preset requires bortle_class"):
        build_location_from_coordinates(
            user_id=100,
            name="Поле",
            latitude=45.0,
            longitude=39.0,
            sky_preset=SkyPreset.CUSTOM_BORTLE,
            bortle_class=None,
            enabled_for_subscription=True,
            created_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
        )
