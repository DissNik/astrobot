# Astrobot

Telegram bot for astronomy trip forecasts.

## Local Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` before running the completed application workflow. This Task 1 scaffold does not
include the migration script or bot entrypoint yet; they are part of the intended app workflow:

```bash
.venv/bin/python scripts/run_migrations.py
.venv/bin/python -m bot.main
```

Run tests:

```bash
.venv/bin/pytest
```

## systemd

```ini
[Unit]
Description=Astrobot Telegram Bot
After=network.target

[Service]
WorkingDirectory=/opt/astrobot
EnvironmentFile=/opt/astrobot/.env
ExecStart=/opt/astrobot/.venv/bin/python -m bot.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
