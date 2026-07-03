"""Admin routes for browsing the application logs (read-only)."""

# Standard library imports
import logging
from datetime import datetime, timezone

# Third-party imports
from flask import render_template, request

# Local imports
from config.constants import ADMIN_PAGE_SIZE
from website.services.app_log import AppLogService
from website.views.admin import admin_bp, get_list_params
from website.views.auth import require_permission

app_log_service = AppLogService()

#: Levels offered by the filter dropdown, in increasing severity.
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def _parse_utc_datetime(value: str) -> datetime | None:
    """Parse an HTML ``datetime-local`` value as a UTC datetime.

    Args:
        value: Raw query-string value (e.g. ``2026-07-03T14:30``).

    Returns:
        Timezone-aware UTC datetime, or None when absent/invalid.
    """
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


@admin_bp.route("/app-logs/", methods=["GET"])
@require_permission("app_log.view")
def list_app_logs():
    """List the application logs with level/date filters and pagination."""
    page, search = get_list_params()
    level = (request.args.get("level") or "").strip().upper()
    if level not in LOG_LEVELS:
        level = ""
    start_raw = (request.args.get("start") or "").strip()
    end_raw = (request.args.get("end") or "").strip()
    logger_filter = (request.args.get("logger") or "").strip()

    pagination = app_log_service.list_paginated(
        page=page,
        per_page=ADMIN_PAGE_SIZE,
        level_no=logging.getLevelNamesMapping()[level] if level else None,
        start=_parse_utc_datetime(start_raw),
        end=_parse_utc_datetime(end_raw),
        logger=logger_filter or None,
        search=search,
    )
    # Non-empty filters only, so pager links stay clean and preserve state.
    filter_args = {
        key: value
        for key, value in (
            ("level", level),
            ("start", start_raw),
            ("end", end_raw),
            ("logger", logger_filter),
            ("q", search),
        )
        if value
    }
    return render_template(
        "admin/app_logs/list.html",
        pagination=pagination,
        levels=LOG_LEVELS,
        level=level,
        start=start_raw,
        end=end_raw,
        logger_filter=logger_filter,
        search=search,
        filter_args=filter_args,
    )
