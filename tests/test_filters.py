import datetime
from website.views.filters import format_datetime


def test_format_datetime():
    """
    Test format_datetime filter.
    """
    date = datetime.datetime(2000, 1, 1, 0, 1)
    f_date = format_datetime(date).lower()
    expected_date = "sam. 01/01 - 00h01"
    assert expected_date == f_date
