# Astrobot

Telegram bot for astronomy trip forecasts.

Astrobot helps pick observing nights for saved locations. It uses Open-Meteo for weather
and geocoding data, scores each night from 0 to 100, and can send scheduled Telegram
alerts.

## Features

- Telegram polling bot built with aiogram.
- Saved observing locations from a city name, coordinates, or Telegram geolocation.
- Per-location forecast reports for 3, 5, or 7 nights.
- Deep-sky and planetary/lunar observing profiles.
- Daily digest or "good conditions only" alerts.
- Per-user language selection: English and Russian.
- Admin statistics for configured owner Telegram IDs.
- SQLite storage with local migrations.

## Commands

- `/start` opens the main menu.
- `/forecast` asks for a saved location and sends the forecast.
- `/locations` opens location management.
- `/subscribe` opens alert controls.
- `/settings` opens profile, language, forecast horizon, alert mode, threshold, and send time settings.
- `/stats` shows bot statistics for configured owners only.

## Configuration

Copy `.env.example` to `.env` and set:

```dotenv
TELEGRAM_BOT_TOKEN=123456:replace-me
OWNER_TELEGRAM_IDS=123456789,987654321
DATABASE_PATH=./data/astrobot.sqlite3
LOG_LEVEL=INFO
```

`OWNER_TELEGRAM_IDS` accepts a comma- or semicolon-separated list. `LOG_LEVEL` must be
one of `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.

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

Run linting:

```bash
.venv/bin/ruff check .
```

## How Forecasts Work

The bot requests hourly cloud cover, high cloud cover, humidity, wind, sunrise, and
sunset from Open-Meteo. Each forecasted night is evaluated from one hour after sunset
to one hour before the next sunrise, so provider requests include one extra day.

The score starts at 100 and applies penalties for cloud cover, high cloud cover, Moon
conditions, sky brightness/Bortle class, humidity, fog risk, and wind. Deep-sky forecasts
penalize Moon brightness and visible Moon more heavily; planetary/lunar forecasts treat
the Moon as non-critical.

## Alerts

The scheduler checks enabled subscriptions once per minute. Users can choose:

- Daily digest: sends all available reports for enabled locations.
- Good conditions only: sends only nights with a score at or above the configured threshold.

The default alert time is `20:00 UTC`. In settings, users can enter a local time and
optionally a timezone, for example `21:30 Europe/Moscow` or `21:30 +5`.

When a subscription is enabled after today's configured send time, the bot records today
as already processed so it does not send an immediate catch-up message.

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
