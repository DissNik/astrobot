import os
import subprocess
import sys
from pathlib import Path


def test_run_migrations_script_imports_project_package(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    database_path = tmp_path / "astrobot.sqlite3"
    env = {
        **os.environ,
        "TELEGRAM_BOT_TOKEN": "123:abc",
        "OWNER_TELEGRAM_IDS": "42,100",
        "DATABASE_PATH": str(database_path),
    }
    env.pop("PYTHONPATH", None)

    result = subprocess.run(
        [sys.executable, "scripts/run_migrations.py"],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert database_path.exists()
