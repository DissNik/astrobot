from bot.domain.enums import ObservingProfile, SubscriptionMode
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
    assert keyboard.is_persistent is None


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
        "settings:open",
    }


def test_subscription_keyboard_marks_current_state_and_links_settings() -> None:
    keyboard = subscription_keyboard("ru", enabled=False)
    rows = [
        [(button.callback_data, button.text) for button in row]
        for row in keyboard.inline_keyboard
    ]

    assert rows[0] == [
        ("subscription:enable", "Включена"),
        ("subscription:disable", "✅ Отключена"),
    ]
    assert rows[1] == [("settings:open", "⚙️ Настройки")]

    enabled_keyboard = subscription_keyboard("ru", enabled=True)
    enabled_labels = {
        button.callback_data: button.text
        for row in enabled_keyboard.inline_keyboard
        for button in row
    }

    assert enabled_labels["subscription:enable"] == "✅ Включена"
    assert enabled_labels["subscription:disable"] == "Отключена"


def test_settings_keyboard_uses_wide_rows_for_long_russian_labels() -> None:
    keyboard = settings_keyboard("ru")
    rows = [[button.callback_data for button in row] for row in keyboard.inline_keyboard]

    assert ["settings:mode:daily_digest"] in rows
    assert ["settings:mode:good_conditions_only"] in rows
    assert ["settings:threshold:50", "settings:threshold:60"] in rows
    assert ["settings:threshold:70", "settings:threshold:80"] in rows


def test_settings_keyboard_marks_selected_values() -> None:
    keyboard = settings_keyboard(
        "ru",
        selected_language="ru",
        forecast_days=5,
        observing_profile=ObservingProfile.PLANETARY_LUNAR,
        mode=SubscriptionMode.GOOD_CONDITIONS_ONLY,
        score_threshold=70,
    )
    labels_by_callback = {
        button.callback_data: button.text
        for row in keyboard.inline_keyboard
        for button in row
    }

    assert labels_by_callback["settings:days:5"] == "✅ 5 ночей"
    assert labels_by_callback["settings:language:ru"] == "✅ Русский"
    assert labels_by_callback["settings:profile:planetary_lunar"] == "✅ Планеты/Луна"
    assert labels_by_callback["settings:mode:good_conditions_only"] == (
        "✅ Только хорошие условия"
    )
    assert labels_by_callback["settings:threshold:70"] == "✅ Порог 70"
    assert labels_by_callback["settings:days:3"] == "3 ночи"
