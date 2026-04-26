# Astrobot

Telegram bot for astronomy trip forecasts.

## Local Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`, then run migrations:

```bash
.venv/bin/python scripts/run_migrations.py
```

Run the bot:

```bash
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
