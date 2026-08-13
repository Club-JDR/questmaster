"""Shared scheduling helpers (time-window overlap checks)."""

from datetime import datetime


def intervals_overlap(
    a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime
) -> bool:
    """Check whether two half-open time intervals overlap.

    Touching endpoints do not count as an overlap (e.g. one session ending
    exactly when another starts is fine).

    Args:
        a_start: Start of the first interval.
        a_end: End of the first interval.
        b_start: Start of the second interval.
        b_end: End of the second interval.

    Returns:
        True if the intervals share any time, False otherwise.
    """
    return a_start < b_end and b_start < a_end
