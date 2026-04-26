from bot.config import Settings
from bot.db.connection import connect
from bot.db.migrations import migrate


def main() -> None:
    settings = Settings()
    connection = connect(settings.database_path)
    migrate(connection)
    connection.close()


if __name__ == "__main__":
    main()
