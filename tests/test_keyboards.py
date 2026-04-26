from bot.keyboards.menu import main_menu_keyboard


def test_main_menu_keyboard_contains_core_actions() -> None:
    keyboard = main_menu_keyboard()
    labels = [button.text for row in keyboard.inline_keyboard for button in row]

    assert "Прогноз" in labels
    assert "Точки" in labels
    assert "Рассылка" in labels
    assert "Настройки" in labels
