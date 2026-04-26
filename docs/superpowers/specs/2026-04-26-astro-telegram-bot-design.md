# Astro Telegram Bot Design

Date: 2026-04-26
Status: Draft approved for planning

## Goal

Build a Telegram bot in Python that helps users decide whether an astronomy trip is worthwhile for their saved observation locations.

The first version uses Open-Meteo only. It must be deployable on a VPS without Docker using Python, a virtual environment, and systemd. The architecture should allow later replacement or extension of weather providers and storage without rewriting Telegram handlers.

## MVP Scope

The bot will:

- accept a location as a city name, coordinates, or Telegram geolocation;
- let each user save multiple observation locations;
- store a name, coordinates, source, sky preset, and optional Bortle class for each location;
- calculate forecasts for 3 nights by default;
- let the user choose a forecast horizon of 3, 5, or 7 nights;
- support `deep-sky` and `planetary/lunar` observing profiles;
- provide manual forecasts on request;
- send daily subscription messages at a user-selected local time;
- support two subscription modes: daily digest and good-conditions-only;
- let users configure the score threshold for good-conditions-only mode, defaulting to `60/100`;
- send one compact subscription message covering all enabled locations;
- provide an owner-only `/stats` command.

Out of scope for the first version:

- meteoblue seeing and jet stream integration;
- Windy integration;
- webhook deployment;
- PostgreSQL;
- broadcast/admin mass messaging;
- full multilingual UI.

## Architecture

Use a modular monolith: one Python process containing the Telegram bot and the scheduler.

Runtime stack:

- Python 3.12;
- aiogram 3 for Telegram;
- httpx for API calls;
- pydantic for typed settings and API data where useful;
- SQLite for storage;
- APScheduler for daily subscription jobs;
- pytest for tests.

Deployment target:

- `venv + systemd` on a VPS;
- polling mode for Telegram;
- `.env` for runtime configuration.

Suggested structure:

```text
astrobot/
  bot/
    main.py
    config.py
    texts/
      ru.py
    handlers/
      start.py
      menu.py
      locations.py
      forecast.py
      subscription.py
      settings.py
      admin.py
    keyboards/
      menu.py
      locations.py
      subscription.py
    services/
      location_service.py
      forecast_service.py
      subscription_service.py
      scoring_service.py
      report_formatter.py
    providers/
      weather_base.py
      open_meteo.py
      geocoding.py
    repositories/
      users.py
      locations.py
      subscriptions.py
      forecast_cache.py
    scheduler/
      jobs.py
      runner.py
    db/
      connection.py
      migrations.py
    domain/
      models.py
      enums.py
  tests/
  scripts/
  .env.example
  requirements.txt
  README.md
```

Telegram handlers must not contain weather calculation logic. They validate input, call services, and send responses. Provider integrations live behind weather/geocoding interfaces. SQLite access lives behind repositories.

## User Flows

Main interaction is a button menu with commands as stable entry points.

Commands:

- `/start`: greeting and main menu;
- `/forecast`: forecast for saved or selected locations;
- `/locations`: location management;
- `/subscribe`: subscription setup;
- `/settings`: general settings;
- `/stats`: owner-only stats.

Location management:

- User can add a location by city, coordinates, or Telegram geolocation.
- Bot asks for a display name.
- Bot asks for sky quality using simple presets and optional exact Bortle class.
- Presets are `city`, `suburb`, and `dark_site`.
- Exact Bortle class is `1..9`.
- User can enable or disable each location for subscriptions.
- User can rename or delete saved locations.

Subscription settings:

- enabled or disabled;
- selected locations;
- local send time;
- mode: `daily_digest` or `good_conditions_only`;
- score threshold for good-conditions-only, default `60`;
- forecast horizon: `3`, `5`, or `7` nights;
- observing profile: `deep-sky` or `planetary/lunar`.

Manual forecast:

- If the user has saved locations, `/forecast` shows selected locations.
- If the user has no saved locations, the bot prompts them to add one.
- The user may also send a city, coordinates, or geolocation for a one-off forecast without saving.

## Data Model

Storage is SQLite in the first version. Application code accesses it through repositories so PostgreSQL can be introduced later with limited changes.

### User

- `telegram_id`;
- `timezone`;
- `language`, default `ru`;
- `forecast_days`, default `3`;
- `observing_profile`, default `deep_sky`;
- `score_threshold`, default `60`;
- `created_at`.

### Location

- `id`;
- `user_id`;
- `name`;
- `latitude`;
- `longitude`;
- `source`: `city`, `coordinates`, or `telegram_geo`;
- `sky_preset`: `city`, `suburb`, `dark_site`, or `custom_bortle`;
- `bortle_class`: nullable integer `1..9`;
- `enabled_for_subscription`;
- `created_at`.

### Subscription

- `user_id`;
- `enabled`;
- `mode`: `daily_digest` or `good_conditions_only`;
- `send_time_local`;
- `forecast_days`: `3`, `5`, or `7`;
- `observing_profile`;
- `score_threshold`;
- `updated_at`.

### ForecastCache

- `location_id`;
- `provider`;
- `forecast_date`;
- `payload_json`;
- `created_at`.

Timezone behavior:

- City geocoding and Open-Meteo forecast responses may provide timezone data.
- For coordinates, use Open-Meteo timezone data for forecast interpretation.
- User timezone is used for subscription scheduling.
- If the user explicitly changes timezone, that value controls scheduling.

Forecast cache is used to avoid duplicate API requests during repeated interactions and to simplify debugging. It is not a correctness dependency.

## Forecast Provider

The MVP provider is Open-Meteo.

Geocoding:

- Resolve city names to coordinates and candidate display names.
- If a city is ambiguous, ask the user to choose from candidates.

Forecast inputs:

- hourly `cloud_cover`;
- hourly `cloud_cover_low`;
- hourly `cloud_cover_mid`;
- hourly `cloud_cover_high`;
- hourly `relative_humidity_2m`;
- hourly `wind_speed_10m`;
- fog or visibility-related fields if available;
- daily `moon_phase`;
- daily `moonrise`;
- daily `moonset`;
- sunrise and sunset or equivalent daily fields;
- timezone set to `auto`.

Provider boundary:

- Open-Meteo returns provider-specific data.
- `forecast_service` converts it into domain-level nightly forecast objects.
- Future meteoblue or Windy adapters should be able to provide the same domain objects or optional extra metrics.

## Night Window

For MVP, define the useful night window as:

- start: `sunset + 1 hour`;
- end: `sunrise - 1 hour`.

This is intentionally practical rather than astronomically perfect. Later versions may use astronomical twilight from a dedicated astronomy library or provider fields if reliable.

All hourly weather aggregates for a night are calculated over this night window in the location timezone.

## Scoring

Each night receives a score from `0` to `100`.

Penalty factors:

- total cloud cover: highest weight;
- high cloud cover: separate penalty;
- moon phase: strong penalty for `deep-sky`, weak or no penalty for `planetary/lunar`;
- moon above horizon during the useful night window: additional `deep-sky` penalty;
- humidity and fog risk;
- wind speed;
- sky quality preset or Bortle class, mainly for `deep-sky`.

Verdicts:

- `80..100`: excellent;
- `60..79`: worth going;
- `40..59`: doubtful;
- `0..39`: not worth going.

The report must explain the score with short reasons: cloud cover, Moon, humidity or fog, wind, and sky quality where relevant.

The initial scoring weights should be explicit constants with unit tests. They can be tuned after observing real forecasts.

## Message Format

Manual forecast and subscription messages are in Russian.

The first version stores text templates separately from business logic so later i18n is possible.

Subscription messages use one compact message for all enabled locations. The message should compare locations and include short details for each location.

Good-conditions-only behavior:

- The scheduler calculates the configured forecast horizon for all enabled subscription locations.
- If no location/night reaches the user's threshold, no message is sent.
- If at least one location/night reaches the threshold, send a compact summary with the best matching nights and locations.

Daily digest behavior:

- Always send the configured forecast summary at the user's selected time.

## Error Handling

- If a city is not found, ask the user to refine the name or send geolocation.
- If multiple geocoding results are plausible, show choices.
- If Open-Meteo is unavailable, show a short temporary error and log details.
- If the user has no saved locations, forecast and subscription flows lead to adding the first location.
- If a subscription send fails, log the error and keep the bot process alive.
- If Telegram indicates the user blocked the bot, mark the subscription disabled or inactive.

## Admin

The owner-only `/stats` command shows:

- number of users;
- number of saved locations;
- number of active subscriptions;
- recent forecast API error count if tracked;
- application version or start time if available.

`OWNER_TELEGRAM_ID` is configured in `.env`.

## Deployment

Primary deployment is without Docker:

1. Install Python 3.12 or compatible Python 3.
2. Create a virtual environment.
3. Install dependencies from `requirements.txt`.
4. Configure `.env`.
5. Run migrations.
6. Start via systemd.

Required environment variables:

- `TELEGRAM_BOT_TOKEN`;
- `OWNER_TELEGRAM_ID`;
- `DATABASE_PATH`;
- `LOG_LEVEL`.

Example systemd service should be documented in `README.md`.

## Testing

Required tests:

- scoring unit tests for both observing profiles;
- night window aggregation tests;
- report formatter tests;
- repository tests using temporary SQLite;
- subscription selection tests for daily digest and good-conditions-only;
- provider tests using mocked Open-Meteo responses;
- smoke test that application setup can initialize without starting real Telegram polling.

Network calls should not be required for the default test suite.

## Open Decisions For Implementation

- Exact scoring weights will be chosen during implementation and covered with tests.
- Exact Russian message text will be written during implementation.
- Whether to use a simple migration module or a lightweight migration tool will be decided during implementation, keeping the first version small.
