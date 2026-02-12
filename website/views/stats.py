import calendar
from collections import Counter, defaultdict
from datetime import datetime

from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta
from flask import Blueprint, jsonify, render_template, request, url_for

from config.constants import GAME_DETAILS_ROUTE
from website.extensions import cache
from website.services.game_session import GameSessionService
from website.views.auth import who

stats_bp = Blueprint("stats", __name__)


def default_game_entry():
    return {"count": 0, "gm": ""}


def default_system_dict():
    return defaultdict(default_game_entry)


@cache.memoize(timeout=3600)
def get_cached_stats_for_period(year, month):
    if year and month:
        base_day = datetime(year, month, 1)
    else:
        today = datetime.today()
        base_day = today.replace(day=1)

    last_day = datetime(
        base_day.year,
        base_day.month,
        calendar.monthrange(base_day.year, base_day.month)[1],
        23,
        59,
        59,
        999999,
    )

    sessions = GameSessionService().find_in_range(base_day, last_day)

    num_os = 0
    num_campaign = 0
    os_games = defaultdict(default_system_dict)
    campaign_games = defaultdict(default_system_dict)

    gm_names = []

    for session in sessions:
        game = session.game
        system = game.system.name
        slug = game.slug
        game_name = game.name
        gm_name = game.gm.name
        entry = {"name": game_name, "gm": gm_name, "count": 1}

        if game.type == "oneshot":
            num_os += 1
            if slug in os_games[system]:
                os_games[system][slug]["count"] += 1
            else:
                os_games[system][slug] = entry
        else:
            num_campaign += 1
            if slug in campaign_games[system]:
                campaign_games[system][slug]["count"] += 1
            else:
                campaign_games[system][slug] = entry

        gm_names.append(gm_name)

    return {
        "base_day": base_day,
        "last_day": last_day,
        "num_os": num_os,
        "num_campaign": num_campaign,
        "os_games": os_games,
        "campaign_games": campaign_games,
        "gm_names": gm_names,
    }


@stats_bp.route("/stats/", methods=["GET"])
def get_stats():
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)

    stats = get_cached_stats_for_period(year, month)

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


@stats_bp.route("/calendrier/")
def get_calendar():
    payload = who()
    return render_template("calendar.j2", payload=payload)


@stats_bp.route("/calendrier/widget/")
def get_calendar_widget():
    return render_template("calendar_widget.j2")


@stats_bp.route("/api/calendar/")
@cache.cached(query_string=True)
def get_month_games_json():
    # Get the start and end from query parameters
    start_str = request.args.get("start")
    end_str = request.args.get("end")

    if not start_str or not end_str:
        return jsonify([]), 400

    try:
        start = parse_date(start_str)
        end = parse_date(end_str)
    except ValueError:
        return jsonify([]), 400

    sessions = GameSessionService().find_in_range(start, end)

    events = []
    for session in sessions:
        start = session.start
        end = session.end

        # If it crosses midnight, force the end to same day
        if end.date() > start.date():
            end = start.replace(hour=23, minute=59, second=59)

        events.append(
            {
                "id": session.id,
                "title": f"{session.game.name} par {session.game.gm.name}",
                "start": start.isoformat(),
                "end": end.isoformat(),
                "color": "#75b798" if session.game.type == "oneshot" else "#0d6efd",
                "className": (
                    "event-oneshot" if session.game.type == "oneshot" else "event-campaign"
                ),
                "url": url_for(GAME_DETAILS_ROUTE, slug=session.game.slug),
            }
        )

    return jsonify(events)
