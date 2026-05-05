# Standard Menu Format Design

## Goal

Standardize Astrobot menu messages so they share one visual structure: bold icon title,
optional divider, existing body text, and unchanged existing buttons.

## Scope

This applies to interactive menu messages that present Telegram buttons:

- main menu;
- forecast location chooser;
- locations list;
- location details;
- subscription menu;
- settings menu.

Forecast reports and transient input prompts are out of scope because they are content messages, not
menus.

## Format

Menu text must be rendered as HTML:

```text
<b>{icon} {title}</b>
____________

{body}
```

If the menu has no body text, only the bold title is sent and the divider is omitted.

Existing body text, callback data, and keyboard layouts must not change except for being placed below
the common title and divider.

## Implementation Approach

Add a small handler presentation helper for menu formatting. The helper owns HTML escaping and the
divider rule so individual handlers cannot drift.

Handler functions should continue to own feature-specific text values and keyboard selection.

## Testing

Update handler tests to assert:

- menu messages use the bold HTML title;
- messages with body include the divider;
- title-only menus omit the divider;
- keyboards and callback data remain unchanged.

Run targeted handler tests, then run the full suite and Ruff.
