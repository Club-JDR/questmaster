"""Statistics and calendar views."""

from collections import Counter

from dateutil.relativedelta import relativedelta
from flask import Blueprint, render_template, request

from website.services.game_session import GameSessionService
from website.views.auth import who

stats_bp = Blueprint("stats", __name__)

# Service instances
session_service = GameSessionService()


@stats_bp.route("/stats/", methods=["GET"])
def get_stats():
    """Render monthly statistics page."""
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)

    stats = session_service.get_stats_for_period(year, month)

    base_day = stats["base_day"]
    last_day = stats["last_day"]
    prev_month_date = base_day - relativedelta(months=1)
    next_month_date = base_day + relativedelta(months=1)

    return render_template(
        "stats.j2",
        base_day=base_day.strftime("%B %Y"),
        last_day=last_day.strftime("%a %d/%m"),
        num_os=stats["num_os"],
        num_campaign=stats["num_campaign"],
        os=stats["os_games"],
        campaign=stats["campaign_games"],
        mjs=sorted(Counter(stats["gm_names"]).items(), key=lambda x: x[1], reverse=True),
        year=base_day.year,
        month=base_day.month,
        prev_year=prev_month_date.year,
        prev_month=prev_month_date.month,
        next_year=next_month_date.year,
        next_month=next_month_date.month,
    )


@stats_bp.route("/calendrier/", methods=["GET"])
def get_calendar():
    """Render the interactive calendar page."""
    payload = who()
    return render_template("calendar.j2", payload=payload)


@stats_bp.route("/calendrier/widget/", methods=["GET"])
def get_calendar_widget():
    """Render the embeddable calendar widget."""
    return render_template("calendar_widget.j2")
