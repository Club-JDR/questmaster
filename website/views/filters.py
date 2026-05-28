"""Jinja2 template filters for date formatting and color utilities."""

import locale
from datetime import datetime
from zoneinfo import ZoneInfo


def format_datetime(value, format="%a %d/%m - %Hh%M"):
    """Format a datetime for display in French locale.

    Accepts both ``datetime`` objects and ISO 8601 strings (as returned
    by model ``to_dict()`` serialization).

    Args:
        value: Datetime object or ISO 8601 string to format.
        format: strftime format string. Defaults to '%a %d/%m - %Hh%M'.

    Returns:
        Formatted date string (e.g. 'Sam 10/09 - 20h30').
    """
    if value is None:
        return ""
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
    if hasattr(value, "tzinfo") and value.tzinfo is not None:
        value = value.astimezone(ZoneInfo("Europe/Paris"))
    return value.strftime(format)


def duration_hours(start, end):
    """Return duration between two datetimes rounded to the nearest half-hour.

    Accepts both ``datetime`` objects and ISO 8601 strings.

    Args:
        start: Start datetime or ISO 8601 string.
        end: End datetime or ISO 8601 string.

    Returns:
        Duration in hours as a float rounded to the nearest 0.5 (e.g. 2.5, 3.0).
    """
    if isinstance(start, str):
        start = datetime.fromisoformat(start)
    if isinstance(end, str):
        end = datetime.fromisoformat(end)
    hours = (end - start).total_seconds() / 3600
    return round(hours * 2) / 2


def hex_color(int_color):
    """Convert an integer (e.g. 0x198754) to a hex string like '#198754'."""
    if int_color is None:
        return None
    return f"#{int_color:06x}"


def text_color(bg_hex):
    """Return 'black' or 'white' depending on background brightness."""
    if not bg_hex or not bg_hex.startswith("#"):
        return "black"
    bg_hex = bg_hex.lstrip("#")
    r, g, b = (int(bg_hex[i : i + 2], 16) for i in (0, 2, 4))
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return "black" if brightness > 128 else "white"
