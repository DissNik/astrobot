from bot.keyboards.locations import locations_keyboard
from bot.keyboards.menu import main_menu_keyboard
from bot.keyboards.subscription import subscription_keyboard


def test_main_menu_keyboard_contains_core_actions() -> None:
    keyboard = main_menu_keyboard()
    labels = [button.text for row in keyboard.inline_keyboard for button in row]

    assert "Прогноз" in labels
    assert "Точки" in labels
    assert "Рассылка" in labels
    assert "Настройки" in labels


def test_keyboards_emit_known_callback_data() -> None:
    callback_data = {
        button.callback_data
        for keyboard in (main_menu_keyboard(), locations_keyboard(), subscription_keyboard())
        for row in keyboard.inline_keyboard
        for button in row
    }

    assert callback_data == {
        "forecast:open",
        "locations:open",
        "settings:open",
        "subscription:open",
        "locations:add",
        "locations:list",
        "subscription:enable",
        "subscription:disable",
        "menu:open",
    }
