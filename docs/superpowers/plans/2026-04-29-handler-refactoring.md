# Handler Refactoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce duplication in Astrobot handlers while preserving current Telegram behavior.

**Architecture:** Add small handler-only utilities for Telegram/user concerns, and move subscription enable/disable workflow construction into `bot/services/subscription_service.py`. Keep handlers as aiogram boundaries and keep feature-specific formatting local.

**Tech Stack:** Python 3.12, aiogram 3, SQLite repositories, pytest, pytest-asyncio, ruff.

---

## File Structure Map

- Create `bot/handlers/common.py`: shared handler helpers for `message_user_id`, language lookup, and safe `edit_text`.
- Create `bot/services/user_service.py`: reusable default-user construction and `ensure_user`.
- Modify `bot/services/subscription_service.py`: add default subscription, enable, disable, and last-sent calculations.
- Modify `bot/handlers/subscription.py`: delegate user/subscription workflow to services and common helpers.
- Modify `bot/handlers/settings.py`: use common helpers and shared user/subscription service helpers.
- Modify `bot/handlers/locations.py`: use common helpers and shared user service helper.
- Modify `tests/test_subscription_service.py`: cover moved subscription workflow behavior.
- Modify `tests/test_subscription_handler.py`: import moved helper from service module.

---

### Task 1: Add Service Tests For Subscription Workflow

**Files:**
- Modify: `tests/test_subscription_service.py`

- [ ] **Step 1: Add tests for subscription workflow helpers**

Append these tests to `tests/test_subscription_service.py`:

```python
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from bot.domain.enums import ObservingProfile, SubscriptionMode
from bot.domain.models import Subscription, User
from bot.services.subscription_service import (
    disable_subscription,
    enable_subscription,
    last_sent_on_for_enabled_subscription,
)


def test_enable_subscription_preserves_existing_settings_after_configured_time() -> None:
    user = User(
        telegram_id=100,
        timezone="Europe/Moscow",
        language="ru",
        forecast_days=5,
        observing_profile=ObservingProfile.PLANETARY_LUNAR,
        score_threshold=70,
        created_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
    )
    current = Subscription(
        user_id=100,
        enabled=False,
        mode=SubscriptionMode.GOOD_CONDITIONS_ONLY,
        send_time_local=time(12, 52),
        forecast_days=5,
        observing_profile=ObservingProfile.PLANETARY_LUNAR,
        score_threshold=70,
        updated_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
    )

    subscription = enable_subscription(
        user,
        current,
        now_utc=datetime(2026, 4, 26, 12, 0, tzinfo=ZoneInfo("UTC")),
    )

    assert subscription.enabled is True
    assert subscription.mode is SubscriptionMode.GOOD_CONDITIONS_ONLY
    assert subscription.send_time_local == time(12, 52)
    assert subscription.forecast_days == 5
    assert subscription.observing_profile is ObservingProfile.PLANETARY_LUNAR
    assert subscription.score_threshold == 70
    assert subscription.last_sent_on == date(2026, 4, 26)


def test_disable_subscription_preserves_existing_settings() -> None:
    user = User(
        telegram_id=100,
        timezone="UTC",
        language="en",
        forecast_days=3,
        observing_profile=ObservingProfile.DEEP_SKY,
        score_threshold=60,
        created_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
    )
    current = Subscription(
        user_id=100,
        enabled=True,
        mode=SubscriptionMode.GOOD_CONDITIONS_ONLY,
        send_time_local=time(9, 3),
        forecast_days=7,
        observing_profile=ObservingProfile.PLANETARY_LUNAR,
        score_threshold=80,
        updated_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
        last_sent_on=date(2026, 4, 25),
    )

    subscription = disable_subscription(
        user,
        current,
        now_utc=datetime(2026, 4, 26, 12, 0, tzinfo=ZoneInfo("UTC")),
    )

    assert subscription.enabled is False
    assert subscription.mode is SubscriptionMode.GOOD_CONDITIONS_ONLY
    assert subscription.send_time_local == time(9, 3)
    assert subscription.forecast_days == 7
    assert subscription.observing_profile is ObservingProfile.PLANETARY_LUNAR
    assert subscription.score_threshold == 80
    assert subscription.last_sent_on == date(2026, 4, 25)


def test_last_sent_on_for_enabled_subscription_handles_invalid_timezone() -> None:
    user = User(
        telegram_id=100,
        timezone="Invalid/Timezone",
        language="en",
        forecast_days=3,
        observing_profile=ObservingProfile.DEEP_SKY,
        score_threshold=60,
        created_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
    )
    subscription = Subscription(
        user_id=100,
        enabled=False,
        mode=SubscriptionMode.DAILY_DIGEST,
        send_time_local=time(11, 0),
        forecast_days=3,
        observing_profile=ObservingProfile.DEEP_SKY,
        score_threshold=60,
        updated_at=datetime(2026, 4, 26, tzinfo=ZoneInfo("UTC")),
    )

    result = last_sent_on_for_enabled_subscription(
        subscription,
        user,
        now_utc=datetime(2026, 4, 26, 12, 0, tzinfo=ZoneInfo("UTC")),
    )

    assert result == date(2026, 4, 26)
```

- [ ] **Step 2: Run the new tests and verify they fail**

Run:

```bash
.venv/bin/pytest tests/test_subscription_service.py -v
```

Expected: import failure for `enable_subscription`, `disable_subscription`, or
`last_sent_on_for_enabled_subscription`.

- [ ] **Step 3: Commit failing tests only if the project convention allows red commits**

Do not commit a failing state in this repository. Continue to Task 2.

---

### Task 2: Add User And Handler Helper Modules

**Files:**
- Create: `bot/handlers/common.py`
- Create: `bot/services/user_service.py`
- Test indirectly through existing handler tests and Task 3 service tests.

- [ ] **Step 1: Create common handler helpers**

Create `bot/handlers/common.py`:

```python
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message

from bot.repositories.users import UserRepository
from bot.texts.i18n import DEFAULT_LANGUAGE, normalize_language


def message_user_id(message: Message) -> int | None:
    if message.from_user is None:
        return None
    return message.from_user.id


def language_for_user(user_id: int | None, users: UserRepository | None) -> str:
    if user_id is None or users is None:
        return DEFAULT_LANGUAGE
    user = users.get(user_id)
    if user is None:
        return DEFAULT_LANGUAGE
    return normalize_language(user.language)


def language_for_message(message: Message, users: UserRepository | None) -> str:
    return language_for_user(message_user_id(message), users)


async def edit_callback_message(message: Message, text_value: str, reply_markup=None) -> None:  # noqa: ANN001
    try:
        await message.edit_text(text_value, reply_markup=reply_markup)
    except TelegramBadRequest as error:
        if "message is not modified" not in str(error):
            raise
```

- [ ] **Step 2: Create reusable user default helper**

Create `bot/services/user_service.py`:

```python
from datetime import UTC, datetime

from bot.domain.enums import ObservingProfile
from bot.domain.models import User
from bot.repositories.users import UserRepository
from bot.texts.i18n import DEFAULT_LANGUAGE


def build_default_user(user_id: int, now: datetime | None = None) -> User:
    return User(
        telegram_id=user_id,
        timezone="UTC",
        language=DEFAULT_LANGUAGE,
        forecast_days=3,
        observing_profile=ObservingProfile.DEEP_SKY,
        score_threshold=60,
        created_at=now or datetime.now(tz=UTC),
    )


def ensure_user(user_id: int, users: UserRepository, now: datetime | None = None) -> User:
    user = users.get(user_id)
    if user is not None:
        return user

    user = build_default_user(user_id, now)
    users.upsert(user)
    return user
```

- [ ] **Step 3: Run handler tests to confirm helper modules do not affect behavior yet**

Run:

```bash
.venv/bin/pytest tests/test_settings_handler.py tests/test_locations_handler.py tests/test_subscription_handler.py -v
```

Expected: existing tests pass because handlers have not been changed yet.

---

### Task 3: Move Subscription Workflow To Service Layer

**Files:**
- Modify: `bot/services/subscription_service.py`
- Modify: `bot/handlers/subscription.py`
- Modify: `tests/test_subscription_handler.py`

- [ ] **Step 1: Implement subscription workflow helpers**

In `bot/services/subscription_service.py`, keep `select_reports_for_subscription` and add:

```python
from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from bot.domain.enums import ObservingProfile, SubscriptionMode
from bot.domain.models import LocationForecast, Subscription, User


def build_default_subscription(
    user: User,
    current: Subscription | None = None,
    now_utc: datetime | None = None,
) -> Subscription:
    now = now_utc or datetime.now(tz=UTC)
    return Subscription(
        user_id=user.telegram_id,
        enabled=current.enabled if current else False,
        mode=current.mode if current else SubscriptionMode.DAILY_DIGEST,
        send_time_local=current.send_time_local if current else time(20, 0),
        forecast_days=current.forecast_days if current else user.forecast_days,
        observing_profile=current.observing_profile if current else user.observing_profile,
        score_threshold=current.score_threshold if current else user.score_threshold,
        updated_at=now,
        last_sent_on=current.last_sent_on if current else None,
    )


def enable_subscription(
    user: User,
    current: Subscription | None,
    now_utc: datetime | None = None,
) -> Subscription:
    now = now_utc or datetime.now(tz=UTC)
    base = build_default_subscription(user, current, now)
    return Subscription(
        user_id=base.user_id,
        enabled=True,
        mode=base.mode,
        send_time_local=base.send_time_local,
        forecast_days=base.forecast_days,
        observing_profile=base.observing_profile,
        score_threshold=base.score_threshold,
        updated_at=now,
        last_sent_on=last_sent_on_for_enabled_subscription(base, user, now),
    )


def disable_subscription(
    user: User,
    current: Subscription | None,
    now_utc: datetime | None = None,
) -> Subscription:
    now = now_utc or datetime.now(tz=UTC)
    base = build_default_subscription(user, current, now)
    return Subscription(
        user_id=base.user_id,
        enabled=False,
        mode=base.mode,
        send_time_local=base.send_time_local,
        forecast_days=base.forecast_days,
        observing_profile=base.observing_profile,
        score_threshold=base.score_threshold,
        updated_at=now,
        last_sent_on=base.last_sent_on,
    )


def last_sent_on_for_enabled_subscription(
    subscription: Subscription,
    user: User,
    now_utc: datetime,
) -> date | None:
    timezone = _safe_timezone(user.timezone)
    local_now = now_utc.astimezone(timezone)
    local_today = local_now.date()
    if subscription.last_sent_on == local_today:
        return subscription.last_sent_on
    if local_now.time().replace(second=0, microsecond=0) >= subscription.send_time_local:
        return local_today
    return subscription.last_sent_on


def _safe_timezone(timezone: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")
```

If duplicate imports appear, merge them so `ruff` keeps imports sorted.

- [ ] **Step 2: Update subscription handler imports and callbacks**

In `bot/handlers/subscription.py`:

- remove local `ZoneInfo`, `ZoneInfoNotFoundError`, `ObservingProfile`, `User`, and inline workflow imports that are no longer needed;
- import shared helpers:

```python
from bot.handlers.common import edit_callback_message, language_for_message, language_for_user
from bot.services.subscription_service import (
    build_default_subscription,
    disable_subscription,
    enable_subscription,
)
from bot.services.user_service import ensure_user
```

Change `enable_subscription_callback` body to:

```python
user = ensure_user(callback.from_user.id, users)
language = normalize_language(user.language)
subscription = enable_subscription(user, subscriptions.get(callback.from_user.id))
subscriptions.upsert(subscription)
connection.commit()
if callback.message:
    await edit_callback_message(
        callback.message,
        _format_subscription_menu_for_values(subscription, user.timezone, language),
        reply_markup=subscription_keyboard(language),
    )
await callback.answer()
```

Change `disable_subscription_callback` body to:

```python
user = ensure_user(callback.from_user.id, users)
language = normalize_language(user.language)
subscription = disable_subscription(user, subscriptions.get(callback.from_user.id))
subscriptions.upsert(subscription)
connection.commit()
if callback.message:
    await edit_callback_message(
        callback.message,
        _format_subscription_menu_for_values(subscription, user.timezone, language),
        reply_markup=subscription_keyboard(language),
    )
await callback.answer()
```

Add this local helper to `bot/handlers/subscription.py`:

```python
def _subscription_for_menu(
    user_id: int | None,
    user: User | None,
    subscription: Subscription | None,
) -> Subscription:
    if subscription is not None:
        return subscription

    fallback_user = user or build_default_user(user_id or 0)
    return build_default_subscription(fallback_user)
```

Import `build_default_user` and keep `User`/`Subscription` imports if this helper uses them:

```python
from bot.domain.models import Subscription, User
from bot.services.user_service import build_default_user, ensure_user
```

Change `_format_subscription_menu` to use the helper:

```python
def _format_subscription_menu(
    user_id: int | None,
    users: UserRepository | None,
    subscriptions: SubscriptionRepository | None,
) -> str:
    language = language_for_user(user_id, users)
    user = users.get(user_id) if user_id is not None and users is not None else None
    subscription = (
        subscriptions.get(user_id)
        if user_id is not None and subscriptions is not None
        else None
    )
    timezone = user.timezone if user else "UTC"
    return _format_subscription_menu_for_values(
        _subscription_for_menu(user_id, user, subscription),
        timezone,
        language,
    )
```

Remove the old inline default `Subscription(...)` construction from `_format_subscription_menu`.

- [ ] **Step 3: Keep handler tests importing the moved last-sent helper**

In `tests/test_subscription_handler.py`, replace:

```python
from bot.handlers.subscription import (
    _last_sent_on_for_enabled_subscription,
    disable_subscription_callback,
    enable_subscription_callback,
    subscription_callback,
)
```

with:

```python
from bot.handlers.subscription import (
    disable_subscription_callback,
    enable_subscription_callback,
    subscription_callback,
)
from bot.services.subscription_service import last_sent_on_for_enabled_subscription
```

Replace calls to `_last_sent_on_for_enabled_subscription(...)` with
`last_sent_on_for_enabled_subscription(...)`.

- [ ] **Step 4: Run subscription tests**

Run:

```bash
.venv/bin/pytest tests/test_subscription_service.py tests/test_subscription_handler.py -v
```

Expected: all tests pass.

---

### Task 4: Replace Duplicate Handler Helpers In Settings And Locations

**Files:**
- Modify: `bot/handlers/settings.py`
- Modify: `bot/handlers/locations.py`

- [ ] **Step 1: Update settings handler helper usage**

In `bot/handlers/settings.py`:

- import shared helpers:

```python
from bot.handlers.common import edit_callback_message, language_for_user, message_user_id
from bot.services.subscription_service import build_default_subscription
from bot.services.user_service import build_default_user
```

- remove local `_message_user_id` and `_language_for_user`;
- replace `_message_user_id(...)` calls with `message_user_id(...)`;
- replace `_language_for_user(...)` calls with `language_for_user(...)`;
- update `_ensure_user` to:

```python
def _ensure_user(user_id: int, users: UserRepository) -> User:
    user = users.get(user_id)
    if user is not None:
        return user
    return build_default_user(user_id)
```

- update `_ensure_subscription` to:

```python
def _ensure_subscription(user: User, subscriptions: SubscriptionRepository) -> Subscription:
    subscription = subscriptions.get(user.telegram_id)
    if subscription is not None:
        return subscription
    return build_default_subscription(user)
```

- update `_send_updated_settings` to call `edit_callback_message(...)` instead of duplicating the
  `try/except TelegramBadRequest` block.

- [ ] **Step 2: Update locations handler helper usage**

In `bot/handlers/locations.py`:

- import shared helpers:

```python
from bot.handlers.common import (
    edit_callback_message,
    language_for_message,
    language_for_user,
    message_user_id,
)
from bot.services.user_service import ensure_user
```

- remove local `_message_user_id`, `_language_for_message`, `_language_for_user`,
  `_edit_callback_message`, and `_ensure_user`;
- replace `_message_user_id(...)` with `message_user_id(...)`;
- replace `_language_for_message(...)` with `language_for_message(...)`;
- replace `_language_for_user(...)` with `language_for_user(...)`;
- replace `_edit_callback_message(...)` with `edit_callback_message(...)`;
- in `add_location_name_message`, replace:

```python
user = _ensure_user(user_id, users, now)
```

with:

```python
user = ensure_user(user_id, users, now)
```

- [ ] **Step 3: Run targeted handler tests**

Run:

```bash
.venv/bin/pytest tests/test_settings_handler.py tests/test_locations_handler.py tests/test_subscription_handler.py -v
```

Expected: all tests pass.

- [ ] **Step 4: Run scheduler-adjacent subscription tests**

Run:

```bash
.venv/bin/pytest tests/test_subscription_service.py tests/test_scheduler_jobs.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Run lint and full test suite**

Run:

```bash
.venv/bin/ruff check .
.venv/bin/pytest
```

Expected: `ruff` reports no issues and the full test suite passes.

- [ ] **Step 6: Commit the refactor**

Run:

```bash
git status --short
git add bot/handlers/common.py bot/services/user_service.py bot/services/subscription_service.py bot/handlers/subscription.py bot/handlers/settings.py bot/handlers/locations.py tests/test_subscription_service.py tests/test_subscription_handler.py docs/superpowers/plans/2026-04-29-handler-refactoring.md
git commit -m "refactor: extract handler workflow helpers"
```
