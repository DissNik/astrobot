# Handler Refactoring Design

## Goal

Refactor the Astrobot handler layer to reduce duplication and keep business workflows out of
aiogram handlers, without changing user-visible behavior.

## Scope

This refactoring targets the current large handler files:

- `bot/handlers/settings.py`
- `bot/handlers/locations.py`
- `bot/handlers/subscription.py`

The work must preserve existing Telegram texts, callback data, keyboard layouts, database schema,
and command behavior.

## Current Problems

The handlers currently mix several responsibilities:

- aiogram routing and message/callback responses;
- repository lookups for language and default users;
- subscription default construction and replacement logic;
- callback value parsing;
- repeated safe `edit_text` handling for Telegram's "message is not modified" error;
- presentation formatting for settings and subscription summaries.

This makes the largest handlers harder to read and increases the chance that future changes drift
between settings and subscription flows.

## Recommended Approach

Use a narrow extraction refactor:

1. Add shared handler utilities for common Telegram/user concerns.
2. Move subscription enable/disable workflow logic into the service layer.
3. Keep handlers as the boundary that translates aiogram events into service calls and Telegram
   responses.
4. Keep formatting close to the feature unless it becomes shared by more than one handler.

This keeps the blast radius low while improving the boundaries already used by the project:
handlers call services, services own workflows, and repositories remain the database access layer.

## Components

### Shared Handler Utilities

Create a small helper module under `bot/handlers/` for handler-only concerns:

- `message_user_id(message) -> int | None`
- `language_for_user(user_id, users) -> str`
- `language_for_message(message, users) -> str`
- `edit_callback_message(message, text_value, reply_markup=None) -> None`

These helpers must not know about feature-specific formatting or business rules.

### User Defaults

Move default-user creation into one reusable service helper so settings, locations, and subscription
flows do not each construct the same `User` object independently.

The helper should:

- return an existing user when present;
- create and upsert a default user when missing;
- preserve the existing default values: UTC timezone, default language, 3 forecast days, deep-sky
  profile, threshold 60.

### Subscription Workflow

Extend `bot/services/subscription_service.py` with helpers for:

- building a default subscription from an existing subscription or user defaults;
- enabling a subscription while preserving existing settings;
- disabling a subscription while preserving existing settings;
- calculating `last_sent_on` when a subscription is enabled after today's send time.

The handler should no longer construct full `Subscription` objects inline.

### Parsing And Formatting

Keep feature-specific callback parsing and summary formatting in the existing handler modules unless
the same logic is used by multiple files. This avoids creating abstractions that only hide simple,
local code.

## Data Flow

Settings update:

1. Handler parses callback data.
2. Handler loads or ensures user/subscription through services.
3. Handler persists changed values through repositories.
4. Handler edits the settings message with the existing keyboard.

Subscription enable/disable:

1. Handler receives callback.
2. Handler ensures user.
3. Handler calls a subscription service function.
4. Handler commits the transaction.
5. Handler edits the subscription menu.

Locations:

1. Handler remains responsible for the FSM flow and Telegram responses.
2. Shared language/user helpers replace duplicate local helper code.
3. Location creation continues to use `build_location_from_coordinates`.

## Error Handling

Telegram edit errors should keep the current behavior: ignore only the known "message is not
modified" error and re-raise all other `TelegramBadRequest` exceptions.

Invalid user input and invalid callback data should continue returning the same alert or message
texts as today.

## Testing

Run targeted tests after refactoring:

- `tests/test_settings_handler.py`
- `tests/test_locations_handler.py`
- `tests/test_subscription_handler.py`
- `tests/test_subscription_service.py`
- `tests/test_scheduler_jobs.py` if subscription service behavior changes scheduler-facing data

Then run:

- `.venv/bin/ruff check .`
- `.venv/bin/pytest`

## Out Of Scope

- Changing Telegram UX, text, callback names, or keyboard layout.
- Changing database schema or migrations.
- Adding dependencies.
- Rewriting aiogram routing structure.
- Moving all formatting into a new presentation layer.
