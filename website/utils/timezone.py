"""Timezone conversion helpers.

The single boundary between wall-clock time (as entered and displayed to
users — always Europe/Paris) and the timezone-aware UTC datetimes stored in
the database and compared against "now". ``Game.date`` and
``GameSession.start``/``end`` are ``DateTime(timezone=True)`` columns: every
read gets back an aware datetime; every write should go through
:func:`to_utc` first, and every display should go through :func:`to_local`
(or :func:`format_local`) first.

Never compare or subtract a naive ``datetime.now()`` against these columns —
use :func:`now_utc` instead, so aware and naive values are never mixed.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

APP_TIMEZONE = ZoneInfo("Europe/Paris")


def now_utc() -> datetime:
    """Return the current time as an aware UTC datetime.

    Returns:
        Timezone-aware ``datetime`` in UTC.
    """
    return datetime.now(timezone.utc)


def to_utc(value: datetime) -> datetime:
    """Convert a datetime to aware UTC, treating naive input as Europe/Paris wall time.

    During the one-hour DST fall-back window (the last Sunday of October, when
    02:00-03:00 wall-clock time occurs twice), a naive value is deliberately
    resolved to its first occurrence — ``fold=0``, the CEST/summer-time
    instant — since plain ``datetime-local`` form inputs and Discord command
    options carry no way to disambiguate which occurrence the user meant.

    Args:
        value: A naive datetime (assumed Europe/Paris wall-clock, e.g. parsed
            from a form or Discord command) or an already-aware datetime in
            any timezone.

    Returns:
        The equivalent timezone-aware datetime in UTC.
    """
    if value.tzinfo is None:
        value = value.replace(tzinfo=APP_TIMEZONE, fold=0)
    return value.astimezone(timezone.utc)


def to_local(value: datetime) -> datetime:
    """Convert a datetime to aware Europe/Paris wall-clock time, for display.

    Args:
        value: A timezone-aware datetime (naive input is treated as already
            UTC, matching the DB column default before any given row's data
            has been migrated).

    Returns:
        The equivalent aware datetime in Europe/Paris.
    """
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(APP_TIMEZONE)


def format_local(value: datetime, fmt: str) -> str:
    """Format a datetime as Europe/Paris wall-clock text.

    Shorthand for ``to_local(value).strftime(fmt)`` — the usual way to render
    an aware ``Game.date``/``GameSession.start``/``end`` value for users,
    Discord embeds, or event logs.

    Args:
        value: Datetime to format (see :func:`to_local` for tz handling).
        fmt: strftime format string.

    Returns:
        Formatted string in Europe/Paris local time.
    """
    return to_local(value).strftime(fmt)


def parse_wall_clock_datetime(raw: str) -> datetime:
    """Parse a ``datetime-local`` form value or an offset-aware ISO string as UTC.

    A bare ``datetime-local`` value (e.g. ``"2026-08-20T19:00"``) has no
    timezone info and is interpreted as Europe/Paris wall-clock time, same as
    :func:`to_utc`. A string that already carries a UTC offset (e.g.
    ``"2026-08-20T19:00:00+00:00"`` from an API client) is trusted as-is and
    converted precisely, instead of being truncated and reinterpreted as
    local time.

    Args:
        raw: Raw form value or ISO 8601 datetime string.

    Returns:
        Timezone-aware UTC datetime.

    Raises:
        ValueError: If the value is missing or not a valid ISO datetime.
    """
    normalized = raw.replace("T", " ").strip()
    try:
        value = datetime.fromisoformat(normalized)
    except ValueError:
        value = datetime.fromisoformat(normalized[:16])
    return to_utc(value)
