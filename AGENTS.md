# AGENTS.md

Instructions for Codex and other agent sessions in this repository.

## Project

- Astrobot: Telegram bot for astronomy trip forecasts.
- Primary language: Python 3.12+.
- Main application code lives in `bot/`.
- Tests live in `tests/`.
- Utility scripts live in `scripts/`.
- Documentation and checklists live in `docs/`.

## Local Environment

- Use the `.venv` virtual environment if it already exists.
- Install dependencies with `.venv/bin/pip install -r requirements.txt`.
- Run migrations with `.venv/bin/python scripts/run_migrations.py`.
- Run the bot with `.venv/bin/python -m bot.main`.
- Before running the bot, configure `.env` from `.env.example`.

## Verification

- Full test run: `.venv/bin/pytest`.
- Linting: `.venv/bin/ruff check .`.
- If response formatting, subscriptions, locations, or forecast logic changes, run the relevant tests from `tests/`, then run the full `pytest` suite when reasonable.
- Before claiming a task is complete, actually run the appropriate checks and report the result.
- Before deployment or user-flow changes, use `docs/manual-test-checklist.md` for manual verification.

## Development Style

- Follow the existing structure: handlers, services, repositories, providers, domain, scheduler.
- Keep business logic in services/domain and keep handlers thin.
- Use the provider layer for external APIs; do not spread HTTP calls across handlers/services without a reason.
- Use the repository layer for data storage access.
- Prefer explicit types and pydantic models where they are already used.
- Do not add new dependencies without a strong reason.
- Follow the Ruff configuration: line length 100, Python target 3.12, rules `E`, `F`, `I`, `UP`, `B`.

## Working With Changes

- Do not revert user changes unless explicitly asked.
- Before editing, inspect the current file context and nearby tests.
- Make minimal, targeted changes within the task scope.
- If behavior changes, add or update tests next to existing tests for the same area.
- If tests require network access or real tokens, mock external calls and do not use real secrets.

## Security and Secrets

- Do not commit `.env`, Telegram tokens, API keys, or personal data.
- Do not print secrets in logs, test snapshots, or responses to the user.
- Use placeholders in examples.

## Communication

- Write briefly and concretely.
- In the final response, state which files changed and which checks were run.
- If a check could not be run, clearly say why.
