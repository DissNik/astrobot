import pytest

from bot.handlers.locations import AddLocationStates
from bot.middlewares.menu_state import MainMenuStateResetMiddleware


class FakeUser:
    def __init__(self, user_id: int) -> None:
        self.id = user_id


class FakeMessage:
    def __init__(self, text: str) -> None:
        self.text = text
        self.from_user = FakeUser(100)


class FakeState:
    def __init__(self, state: object | None) -> None:
        self.state = state
        self.cleared = False

    async def get_state(self) -> object | None:
        return self.state

    async def clear(self) -> None:
        self.state = None
        self.cleared = True


@pytest.mark.asyncio
async def test_main_menu_message_clears_pending_location_state() -> None:
    middleware = MainMenuStateResetMiddleware()
    state = FakeState(AddLocationStates.waiting_for_location_input)
    handled = False

    async def handler(message: FakeMessage, data: dict) -> str:
        nonlocal handled
        handled = True
        assert data["state"].state is None
        return "ok"

    result = await middleware(handler, FakeMessage("📬 Рассылка"), {"state": state})

    assert result == "ok"
    assert handled is True
    assert state.cleared is True


@pytest.mark.asyncio
async def test_regular_message_keeps_pending_location_state() -> None:
    middleware = MainMenuStateResetMiddleware()
    state = FakeState(AddLocationStates.waiting_for_location_input)

    async def handler(message: FakeMessage, data: dict) -> str:
        return "ok"

    result = await middleware(handler, FakeMessage("Екатеринбург"), {"state": state})

    assert result == "ok"
    assert state.cleared is False
    assert state.state == AddLocationStates.waiting_for_location_input
