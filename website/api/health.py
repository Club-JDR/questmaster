"""API health check endpoint."""

import os
from datetime import datetime, timezone

import psutil
from flask import Blueprint, jsonify
from sqlalchemy import text

from website.extensions import db
from website.utils import get_app_version

health_bp = Blueprint("api_health", __name__)


def _format_uptime(seconds: int) -> str:
    """Convert seconds to a human-readable string.

    Args:
        seconds: Number of seconds to convert.

    Returns:
        Formatted string like '1d 2h 30m 15s'.
    """
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return f"{days}d {hours}h {minutes}m {seconds}s"


@health_bp.route("/health/", methods=["GET"])
def health():
    """Return API health status as JSON.

    Returns:
        JSON with status, version, database connectivity, and uptime.
    """
    db_status = "ok"
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    process = psutil.Process(os.getpid())
    uptime_secs = int(
        (datetime.now() - datetime.fromtimestamp(process.create_time())).total_seconds()
    )

    return (
        jsonify(
            {
                "status": "ok",
                "version": get_app_version(),
                "database": db_status,
                "uptime": _format_uptime(uptime_secs),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ),
        200,
    )
