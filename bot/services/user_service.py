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
