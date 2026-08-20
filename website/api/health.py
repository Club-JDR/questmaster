"""API health check endpoint."""

import logging
import os
from datetime import datetime, timezone

import psutil
from flask import Blueprint, jsonify
from sqlalchemy import text

from website.extensions import cache, db
from website.utils import get_app_version

logger = logging.getLogger(__name__)

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


def _check_database() -> bool:
    """Probe the database with a trivial query.

    Returns:
        True if the database responded, False otherwise.
    """
    try:
        db.session.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("Health check: database probe failed")
        return False


def _check_cache() -> bool:
    """Probe the cache backend (Redis) with a round-trip read.

    Returns:
        True if the cache backend responded, False otherwise.
    """
    try:
        cache.get("__health_check__")
        return True
    except Exception:
        logger.exception("Health check: cache probe failed")
        return False


@health_bp.route("/health/", methods=["GET"])
def health():
    """Return API health status as JSON.

    Probes the database and cache backend so the container healthcheck
    (`curl -f`) can actually fail when either is unreachable, instead of
    always seeing a 200 regardless of connectivity.

    Returns:
        JSON with status, version, database/cache connectivity, and uptime.
        HTTP 200 if both dependencies are reachable, 503 otherwise.
    """
    db_ok = _check_database()
    cache_ok = _check_cache()
    healthy = db_ok and cache_ok

    process = psutil.Process(os.getpid())
    uptime_secs = int(
        (datetime.now() - datetime.fromtimestamp(process.create_time())).total_seconds()
    )

    return (
        jsonify(
            {
                "status": "ok" if healthy else "error",
                "version": get_app_version(),
                "database": "ok" if db_ok else "error",
                "cache": "ok" if cache_ok else "error",
                "uptime": _format_uptime(uptime_secs),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ),
        200 if healthy else 503,
    )
