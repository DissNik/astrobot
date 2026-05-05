# Standard Menu Format Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Standardize Telegram menu messages with a bold icon title, optional divider, unchanged body text, and unchanged buttons.

**Architecture:** Add one shared handler presentation helper that formats menu messages and defines the HTML parse mode. Update menu-producing handlers to use it while leaving feature-specific body text and keyboards local.

**Tech Stack:** Python 3.12, aiogram 3, pytest, pytest-asyncio, ruff.

---

## File Structure Map

- Create `bot/handlers/menu_format.py`: shared `format_menu_message` helper and `MENU_PARSE_MODE`.
- Modify `bot/handlers/common.py`: allow `edit_callback_message` to pass `parse_mode`.
- Modify `bot/handlers/menu.py`: format the main menu title.
- Modify `bot/handlers/forecast.py`: format the location chooser.
- Modify `bot/handlers/locations.py`: format location list and location details.
- Modify `bot/handlers/subscription.py`: format subscription menu.
- Modify `bot/handlers/settings.py`: format settings menu.
- Modify focused handler tests for expected menu strings and parse mode where fakes expose it.

### Task 1: Add Failing Tests

- [x] Update tests in `tests/test_settings_handler.py`, `tests/test_subscription_handler.py`,
  `tests/test_locations_handler.py`, `tests/test_forecast_handler.py`, and `tests/test_menu_format.py`
  to expect bold HTML menu titles and divider behavior.
- [x] Run `.venv/bin/pytest tests/test_menu_format.py tests/test_settings_handler.py tests/test_subscription_handler.py tests/test_locations_handler.py tests/test_forecast_handler.py -q`.
- [x] Confirm failures are due to missing `bot.handlers.menu_format` or old message text.

### Task 2: Implement Shared Formatting

- [x] Create `bot/handlers/menu_format.py` with `MENU_PARSE_MODE = "HTML"`,
  `MENU_DIVIDER = "____________"`, and `format_menu_message`.
- [x] Escape title and body with `html.escape`.
- [x] Omit the divider when body is empty or whitespace-only.
- [x] Run `.venv/bin/pytest tests/test_menu_format.py -q`.

### Task 3: Apply Formatting To Menus

- [x] Update handlers to use `format_menu_message` and `MENU_PARSE_MODE`.
- [x] Pass `parse_mode=MENU_PARSE_MODE` for menu `answer` and `edit_text` calls.
- [x] Preserve all existing keyboard builders, button labels, and callback data.
- [x] Run targeted handler tests.

### Task 4: Verify

- [x] Run `.venv/bin/ruff check .`.
- [x] Run `.venv/bin/pytest`.
- [x] Report changed files and check results.
