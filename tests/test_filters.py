import datetime, locale
from website.views.filters import format_datetime, text_color, hex_color


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


def test_hex_color_int_input():
    # Basic integer
    assert hex_color(0x198754) == "#198754"
    assert hex_color(0x000000) == "#000000"
    assert hex_color(0xFFFFFF) == "#ffffff"
    # None returns None
    assert hex_color(None) is None
    # Small numbers are padded
    assert hex_color(0x1A2) == "#0001a2"


def test_text_color_with_dark_bg():
    # Very dark background -> white text
    assert text_color("#000000") == "white"
    assert text_color("#123456") == "white"


def test_text_color_with_light_bg():
    # Very light background -> black text
    assert text_color("#ffffff") == "black"
    assert text_color("#cccccc") == "black"


def test_text_color_invalid_input():
    # Invalid inputs -> default to black
    assert text_color(None) == "black"
    assert text_color("") == "black"
    assert text_color("123456") == "black"
