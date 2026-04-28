import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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
