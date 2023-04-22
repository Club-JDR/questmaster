from website import app
import locale, datetime


@app.template_filter("format_datetime")
def format_datetime(value, format="%a %d/%m - %Hh%M"):
    """
    Jinja filter to format date like this: Sam 10/09 - 20h30
    """
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
    return value.strftime(format)
