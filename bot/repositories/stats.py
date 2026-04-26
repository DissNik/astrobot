import sqlite3


class StatsRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def summary(self) -> dict[str, int]:
        users = self.connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        locations = self.connection.execute("SELECT COUNT(*) FROM locations").fetchone()[0]
        active_subscriptions = self.connection.execute(
            "SELECT COUNT(*) FROM subscriptions WHERE enabled = 1"
        ).fetchone()[0]
        return {
            "users": users,
            "locations": locations,
            "active_subscriptions": active_subscriptions,
        }
