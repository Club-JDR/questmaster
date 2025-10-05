from flask import current_app
from markupsafe import Markup
import locale


def format_datetime(value, format="%a %d/%m - %Hh%M"):
    """
    Jinja filter to format date like this: Sam 10/09 - 20h30
    """
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
    return value.strftime(format)


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
