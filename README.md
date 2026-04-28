# Astrobot

Telegram bot for astronomy trip forecasts.

## Local Setup

```bash
python3 --version  # must be 3.12+
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

The MVP uses Telegram polling, so no public domain or HTTPS endpoint is required.

Run tests:

```bash
.venv/bin/pytest
```

## Manual Verification

Use `docs/manual-test-checklist.md` before deploying to a long-running VPS service.

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
