from html import escape

MENU_DIVIDER = "____________"
MENU_PARSE_MODE = "HTML"


def format_menu_message(
    icon: str,
    title: str,
    body: str | None = None,
    *,
    escape_body: bool = True,
) -> str:
    title_text = f"{icon} {title}".strip()
    formatted_title = f"<b>{escape(title_text)}</b>"
    body_text = (body or "").strip()
    if not body_text:
        return formatted_title

    formatted_body = escape(body_text) if escape_body else body_text
    return f"{formatted_title}\n{MENU_DIVIDER}\n\n{formatted_body}"
