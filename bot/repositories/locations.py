import sqlite3
from dataclasses import replace
from datetime import datetime

from bot.domain.enums import LocationSource, SkyPreset
from bot.domain.models import Location


def _row_to_location(row: sqlite3.Row) -> Location:
    return Location(
        id=row["id"],
        user_id=row["user_id"],
        name=row["name"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        source=LocationSource(row["source"]),
        sky_preset=SkyPreset(row["sky_preset"]),
        bortle_class=row["bortle_class"],
        enabled_for_subscription=bool(row["enabled_for_subscription"]),
        created_at=datetime.fromisoformat(row["created_at"]),
    )


class LocationRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def add(self, location: Location) -> Location:
        cursor = self.connection.execute(
            """
            INSERT INTO locations (
                user_id,
                name,
                latitude,
                longitude,
                source,
                sky_preset,
                bortle_class,
                enabled_for_subscription,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                location.user_id,
                location.name,
                location.latitude,
                location.longitude,
                location.source.value,
                location.sky_preset.value,
                location.bortle_class,
                int(location.enabled_for_subscription),
                location.created_at.isoformat(),
            ),
        )
        return replace(location, id=cursor.lastrowid)

    def list_for_user(self, user_id: int) -> list[Location]:
        rows = self.connection.execute(
            "SELECT * FROM locations WHERE user_id = ? ORDER BY id",
            (user_id,),
        ).fetchall()
        return [_row_to_location(row) for row in rows]

    def get_for_user(self, location_id: int, user_id: int) -> Location | None:
        row = self.connection.execute(
            "SELECT * FROM locations WHERE id = ? AND user_id = ?",
            (location_id, user_id),
        ).fetchone()
        if row is None:
            return None
        return _row_to_location(row)

    def rename_for_user(self, location_id: int, user_id: int, name: str) -> None:
        self.connection.execute(
            "UPDATE locations SET name = ? WHERE id = ? AND user_id = ?",
            (name, location_id, user_id),
        )

    def set_subscription_enabled(self, location_id: int, enabled: bool) -> None:
        self.connection.execute(
            "UPDATE locations SET enabled_for_subscription = ? WHERE id = ?",
            (int(enabled), location_id),
        )

    def set_subscription_enabled_for_user(
        self,
        location_id: int,
        user_id: int,
        enabled: bool,
    ) -> None:
        self.connection.execute(
            "UPDATE locations SET enabled_for_subscription = ? WHERE id = ? AND user_id = ?",
            (int(enabled), location_id, user_id),
        )

    def delete(self, location_id: int) -> None:
        self.connection.execute("DELETE FROM locations WHERE id = ?", (location_id,))

    def delete_for_user(self, location_id: int, user_id: int) -> None:
        self.connection.execute(
            "DELETE FROM locations WHERE id = ? AND user_id = ?",
            (location_id, user_id),
        )
