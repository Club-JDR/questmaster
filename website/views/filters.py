from flask import current_app
from zoneinfo import ZoneInfo
import locale


def format_datetime(value, format="%a %d/%m - %Hh%M"):
    """
    Jinja filter to format date like this: Sam 10/09 - 20h30
    """
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
    paris_tz = ZoneInfo("Europe/Paris")
    paris_time = value.astimezone(paris_tz)

    return paris_time.strftime(format)
