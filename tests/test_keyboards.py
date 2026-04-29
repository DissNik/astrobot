from bot.keyboards.locations import locations_keyboard
from bot.keyboards.menu import main_menu_keyboard
from bot.keyboards.settings import settings_keyboard
from bot.keyboards.subscription import subscription_keyboard


def test_main_menu_keyboard_contains_core_actions() -> None:
    keyboard = main_menu_keyboard()
    labels = [button.text for row in keyboard.keyboard for button in row]

    assert "🔭 Forecast" in labels
    assert "📍 Locations" in labels
    assert "📬 Alerts" in labels
    assert "⚙️ Settings" in labels
    assert keyboard.resize_keyboard is True


def test_main_menu_keyboard_supports_russian() -> None:
    keyboard = main_menu_keyboard("ru")
    labels = [button.text for row in keyboard.keyboard for button in row]

    assert "🔭 Прогноз" in labels
    assert "📍 Локации" in labels


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


def test_settings_keyboard_uses_wide_rows_for_long_russian_labels() -> None:
    keyboard = settings_keyboard("ru")
    rows = [[button.callback_data for button in row] for row in keyboard.inline_keyboard]

    assert ["settings:mode:daily_digest"] in rows
    assert ["settings:mode:good_conditions_only"] in rows
    assert ["settings:threshold:50", "settings:threshold:60"] in rows
    assert ["settings:threshold:70", "settings:threshold:80"] in rows
