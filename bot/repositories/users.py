import sqlite3
from datetime import datetime

from bot.domain.enums import ObservingProfile
from bot.domain.models import User


def _row_to_user(row: sqlite3.Row) -> User:
    return User(
        telegram_id=row["telegram_id"],
        timezone=row["timezone"],
        language=row["language"],
        forecast_days=row["forecast_days"],
        observing_profile=ObservingProfile(row["observing_profile"]),
        score_threshold=row["score_threshold"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


class UserRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def upsert(self, user: User) -> None:
        self.connection.execute(
            """
            INSERT INTO users (
                telegram_id,
                timezone,
                language,
                forecast_days,
                observing_profile,
                score_threshold,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                timezone = excluded.timezone,
                language = excluded.language,
                forecast_days = excluded.forecast_days,
                observing_profile = excluded.observing_profile,
                score_threshold = excluded.score_threshold,
                created_at = excluded.created_at
            """,
            (
                user.telegram_id,
                user.timezone,
                user.language,
                user.forecast_days,
                user.observing_profile.value,
                user.score_threshold,
                user.created_at.isoformat(),
            ),
        )
        self.connection.commit()

    def get(self, telegram_id: int) -> User | None:
        row = self.connection.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()
        if row is None:
            return None
        return _row_to_user(row)
