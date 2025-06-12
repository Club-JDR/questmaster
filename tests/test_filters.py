import datetime, locale
from website.views.filters import format_datetime


def test_format_datetime():
    """
    Test format_datetime filter.
    """
    date = datetime.datetime(2000, 1, 1, 0, 1)
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
    f_date = format_datetime(date).lower()
    assert f_date in [
        "sam. 01/01 - 00h01",
        "sam 01/01 - 00h01",
    ]
