"""Helpers for building and validating Discord message components (buttons).

Only **link-style** buttons are supported for now: a button with a label and a
URL that opens the URL when clicked (Discord button style 5). Link buttons need no
interaction handling, so they work over the plain REST API without a gateway
connection — unlike action buttons, which would require a Discord interactions
endpoint.
"""

# Third-party / local imports
from config.constants import (
    DISCORD_BUTTON_LABEL_MAX,
    DISCORD_BUTTON_STYLE_LINK,
    DISCORD_COMPONENT_ACTION_ROW,
    DISCORD_COMPONENT_BUTTON,
    DISCORD_MAX_BUTTONS_PER_ROW,
)
from website.exceptions import ValidationError


def clean_link_buttons(buttons: list[dict]) -> list[dict]:
    """Validate and normalise a list of link-button definitions.

    Empty rows (no label and no URL) are dropped so a partially-filled form does
    not raise; the remaining rows are validated.

    Args:
        buttons: Raw button dicts, each with ``label`` and ``url`` keys.

    Returns:
        A list of cleaned ``{"label", "url"}`` dicts (at most
        :data:`DISCORD_MAX_BUTTONS_PER_ROW`).

    Raises:
        ValidationError: If a button is missing its label or URL, the URL is not an
            http(s) link, a label exceeds the Discord limit, or there are too many
            buttons.
    """
    cleaned: list[dict] = []
    for button in buttons:
        label = (button.get("label") or "").strip()
        url = (button.get("url") or "").strip()
        if not label and not url:
            continue
        if not label:
            raise ValidationError("A button must have a label.", field="button_label")
        if not url:
            raise ValidationError("A button must have a URL.", field="button_url")
        if not url.startswith(("http://", "https://")):
            raise ValidationError(
                "A button URL must start with http:// or https://.", field="button_url"
            )
        if len(label) > DISCORD_BUTTON_LABEL_MAX:
            raise ValidationError(
                f"A button label must be at most {DISCORD_BUTTON_LABEL_MAX} characters.",
                field="button_label",
            )
        cleaned.append({"label": label, "url": url})

    if len(cleaned) > DISCORD_MAX_BUTTONS_PER_ROW:
        raise ValidationError(
            f"A message can have at most {DISCORD_MAX_BUTTONS_PER_ROW} buttons.",
            field="button_label",
        )
    return cleaned


def build_link_button_rows(buttons: list[dict]) -> list[dict]:
    """Build Discord action-row components from cleaned link-button dicts.

    Args:
        buttons: Cleaned ``{"label", "url"}`` dicts (see :func:`clean_link_buttons`).

    Returns:
        A Discord ``components`` list with a single action row of link buttons, or
        an empty list when there are no buttons.
    """
    if not buttons:
        return []
    return [
        {
            "type": DISCORD_COMPONENT_ACTION_ROW,
            "components": [
                {
                    "type": DISCORD_COMPONENT_BUTTON,
                    "style": DISCORD_BUTTON_STYLE_LINK,
                    "label": button["label"],
                    "url": button["url"],
                }
                for button in buttons
            ],
        }
    ]
