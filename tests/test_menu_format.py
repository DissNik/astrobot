from bot.handlers.menu_format import MENU_DIVIDER, format_menu_message


def test_format_menu_message_adds_bold_title_and_divider_for_body() -> None:
    assert format_menu_message("⚙️", "Settings", "Line 1\nLine 2") == (
        "<b>⚙️ Settings</b>\n"
        f"{MENU_DIVIDER}\n"
        "Line 1\n"
        "Line 2"
    )


def test_format_menu_message_omits_divider_without_body() -> None:
    assert format_menu_message("📋", "Main menu") == "<b>📋 Main menu</b>"


def test_format_menu_message_escapes_html() -> None:
    assert format_menu_message("📍", "A < B", "Use > value") == (
        "<b>📍 A &lt; B</b>\n"
        f"{MENU_DIVIDER}\n"
        "Use &gt; value"
    )
