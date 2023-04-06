from website import app
import locale, datetime

@app.template_filter("format_datetime")
def format_datetime(value, format="%A %d %B à %H:%M"):
    """
    Jinja filter to format date like this: Samedi 10 Juin à 20:30
    """
    locale.setlocale(locale.LC_TIME, "fr_FR")
    if value is None:
        return ""
    if isinstance(value, str):
        return datetime.datetime.strftime(format)
    return value.strftime(format)