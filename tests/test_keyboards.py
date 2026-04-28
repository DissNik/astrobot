from bot.keyboards.locations import locations_keyboard
from bot.keyboards.menu import main_menu_keyboard
from bot.keyboards.subscription import subscription_keyboard


def test_main_menu_keyboard_contains_core_actions() -> None:
    keyboard = main_menu_keyboard()
    labels = [button.text for row in keyboard.keyboard for button in row]

    assert "🔭 Прогноз" in labels
    assert "📍 Локации" in labels
    assert "📬 Рассылка" in labels
    assert "⚙️ Настройки" in labels
    assert keyboard.resize_keyboard is True


def test_keyboards_emit_known_callback_data() -> None:
    callback_data = {
        button.callback_data
        for keyboard in (locations_keyboard(), subscription_keyboard())
        for row in keyboard.inline_keyboard
        for button in row
    }

    assert callback_data == {
        "locations:add",
        "locations:list",
        "subscription:enable",
        "subscription:disable",
    }
