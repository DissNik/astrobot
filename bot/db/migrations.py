import sqlite3


def migrate(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            timezone TEXT NOT NULL,
            language TEXT NOT NULL,
            forecast_days INTEGER NOT NULL,
            observing_profile TEXT NOT NULL,
            score_threshold INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            source TEXT NOT NULL,
            sky_preset TEXT NOT NULL,
            bortle_class INTEGER,
            enabled_for_subscription INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_locations_user_id
            ON locations(user_id);

        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id INTEGER PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
            enabled INTEGER NOT NULL,
            mode TEXT NOT NULL,
            send_time_local TEXT NOT NULL,
            forecast_days INTEGER NOT NULL,
            observing_profile TEXT NOT NULL,
            score_threshold INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_subscriptions_enabled
            ON subscriptions(enabled);

        CREATE TABLE IF NOT EXISTS forecast_cache (
            location_id INTEGER NOT NULL,
            provider TEXT NOT NULL,
            forecast_date TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (location_id, provider, forecast_date)
        );

        CREATE INDEX IF NOT EXISTS idx_forecast_cache_lookup
            ON forecast_cache(location_id, provider, forecast_date);
        """
    )
    connection.commit()
