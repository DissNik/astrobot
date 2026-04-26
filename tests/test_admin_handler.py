from bot.handlers.admin import is_owner


def test_is_owner_allows_configured_owner() -> None:
    assert is_owner(user_id=42, owner_id=42) is True


def test_is_owner_rejects_other_users() -> None:
    assert is_owner(user_id=100, owner_id=42) is False
