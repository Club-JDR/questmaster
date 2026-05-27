"""Read-only stats and calendar endpoints for the QuestMaster API."""

from collections import Counter

from dateutil.parser import parse as parse_date
from flask import Blueprint, jsonify, request

from website.api.auth import api_login_optional, api_login_required
from website.exceptions import ValidationError
from website.services.game_session import GameSessionService

stats_bp = Blueprint("api_stats", __name__)

# Service instance
session_service = GameSessionService()


@stats_bp.route("/stats/", methods=["GET"])
@api_login_required
def get_stats():
    """Get monthly game statistics.

    Query parameters:
        year: Year (optional, defaults to current month).
        month: Month (optional, defaults to current month).

    Returns:
        JSON object with period info, game counts, per-system breakdowns,
        and GM leaderboard.
    """
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)

    stats = session_service.get_stats_for_period(year, month)

    gm_leaderboard = sorted(Counter(stats["gm_names"]).items(), key=lambda x: x[1], reverse=True)

    return jsonify(
        {
            "period": {
                "start": stats["base_day"].isoformat(),
                "end": stats["last_day"].isoformat(),
            },
            "counts": {
                "oneshot": stats["num_os"],
                "campaign": stats["num_campaign"],
                "total": stats["num_os"] + stats["num_campaign"],
            },
            "oneshot_games": stats["os_games"],
            "campaign_games": stats["campaign_games"],
            "gm_leaderboard": [{"name": name, "count": count} for name, count in gm_leaderboard],
        }
    )


@stats_bp.route("/calendar/events/", methods=["GET"])
@api_login_optional
def get_calendar_events():
    """Get game sessions for a date range (calendar view).

    Query parameters:
        start: Range start (ISO date string, required).
        end: Range end (ISO date string, required).

    Returns:
        JSON array of calendar event objects.

    Raises:
        ValidationError: If start or end is missing or invalid.
    """
    start_str = request.args.get("start")
    end_str = request.args.get("end")

    if not start_str or not end_str:
        raise ValidationError(
            "Both 'start' and 'end' query parameters are required.",
            field="start,end",
        )

    try:
        start = parse_date(start_str)
        end = parse_date(end_str)
    except ValueError, TypeError:
        raise ValidationError(
            "Invalid date format. Use ISO 8601 (e.g. 2026-01-01).",
            field="start,end",
        )

    sessions = session_service.find_in_range(start, end)

    events = []
    for session in sessions:
        session_start = session.start
        session_end = session.end

        # If it crosses midnight, force the end to same day
        if session_end.date() > session_start.date():
            session_end = session_start.replace(hour=23, minute=59, second=59)

        events.append(
            {
                "id": session.id,
                "title": session.game.name,
                "start": session_start.isoformat(),
                "end": session_end.isoformat(),
                "color": "#75b798" if session.game.type == "oneshot" else "#0d6efd",
                "type": session.game.type,
                "game_slug": session.game.slug,
            }
        )

    return jsonify(events)
