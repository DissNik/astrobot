import json
import sqlite3
from datetime import datetime
from typing import Any


class ForecastCacheRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def save(
        self,
        location_id: int,
        provider: str,
        forecast_date: str,
        payload: dict[str, Any],
        created_at: datetime,
    ) -> None:
        self.connection.execute(
            """
            INSERT INTO forecast_cache (
                location_id,
                provider,
                forecast_date,
                payload,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(location_id, provider, forecast_date) DO UPDATE SET
                payload = excluded.payload,
                created_at = excluded.created_at
            """,
            (
                location_id,
                provider,
                forecast_date,
                json.dumps(payload),
                created_at.isoformat(),
            ),
        )
        self.connection.commit()

    def get(self, location_id: int, provider: str, forecast_date: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            """
            SELECT payload
            FROM forecast_cache
            WHERE location_id = ? AND provider = ? AND forecast_date = ?
            """,
            (location_id, provider, forecast_date),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row["payload"])
