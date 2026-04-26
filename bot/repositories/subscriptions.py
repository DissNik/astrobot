import sqlite3
from datetime import datetime, time

from bot.domain.enums import ObservingProfile, SubscriptionMode
from bot.domain.models import Subscription


def _row_to_subscription(row: sqlite3.Row) -> Subscription:
    return Subscription(
        user_id=row["user_id"],
        enabled=bool(row["enabled"]),
        mode=SubscriptionMode(row["mode"]),
        send_time_local=time.fromisoformat(row["send_time_local"]),
        forecast_days=row["forecast_days"],
        observing_profile=ObservingProfile(row["observing_profile"]),
        score_threshold=row["score_threshold"],
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


class SubscriptionRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def upsert(self, subscription: Subscription) -> None:
        self.connection.execute(
            """
            INSERT INTO subscriptions (
                user_id,
                enabled,
                mode,
                send_time_local,
                forecast_days,
                observing_profile,
                score_threshold,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                enabled = excluded.enabled,
                mode = excluded.mode,
                send_time_local = excluded.send_time_local,
                forecast_days = excluded.forecast_days,
                observing_profile = excluded.observing_profile,
                score_threshold = excluded.score_threshold,
                updated_at = excluded.updated_at
            """,
            (
                subscription.user_id,
                int(subscription.enabled),
                subscription.mode.value,
                subscription.send_time_local.isoformat(),
                subscription.forecast_days,
                subscription.observing_profile.value,
                subscription.score_threshold,
                subscription.updated_at.isoformat(),
            ),
        )

    def get(self, user_id: int) -> Subscription | None:
        row = self.connection.execute(
            "SELECT * FROM subscriptions WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if row is None:
            return None
        return _row_to_subscription(row)

    def list_enabled(self) -> list[Subscription]:
        rows = self.connection.execute(
            "SELECT * FROM subscriptions WHERE enabled = 1 ORDER BY user_id"
        ).fetchall()
        return [_row_to_subscription(row) for row in rows]
