"""Health check endpoint for monitoring."""

import os
from datetime import datetime

import psutil
from flask import Blueprint, jsonify
from sqlalchemy.sql import text

from website.extensions import db
from website.utils import get_app_version

health_bp = Blueprint("health", __name__)


def dhms_from_seconds(seconds) -> str:
    """Convert seconds to a human-readable d:h:m:s string.

    Args:
        seconds: Number of seconds to convert.

    Returns:
        Formatted string like '1 days, 2 hours, 30 minutes, 15 seconds'.
    """
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"


@health_bp.route("/health/", methods=["GET"])
def health():
    """Return application health status as JSON."""
    start_time = psutil.Process(os.getpid()).create_time()
    delta = datetime.now() - datetime.fromtimestamp(start_time)
    uptime = dhms_from_seconds(delta.seconds)
    now = datetime.now().strftime("%Y-%m-%d:%H:%M:%S")
    db_status = "OK"
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        db_status = "ERROR"
    return (
        jsonify(
            {
                "title": "QuestMaster",
                "version": get_app_version(),
                "status": "OK",
                "database": db_status,
                "uptime": uptime,
                "date": now,
            }
        ),
        200,
    )
