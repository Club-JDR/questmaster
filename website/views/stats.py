from flask import render_template, Blueprint, jsonify, request, url_for
from website.models import GameSession
from website.views.auth import who
from website.extensions import cache
from website.views.games.helpers import GAME_DETAILS_ROUTE
from datetime import datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict, Counter
from dateutil.parser import parse as parse_date
import calendar

stats_bp = Blueprint("stats", __name__)


@stats_bp.route("/stats/", methods=["GET"])
@cache.cached(query_string=True)
def get_stats():
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)

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
        999999,  # fix to avoid missing data on the last day
    )

    sessions = GameSession.query.filter(
        GameSession.start >= base_day, GameSession.end <= last_day
    ).all()

    num_os = 0
    num_campaign = 0
    os_games = defaultdict(lambda: defaultdict(lambda: {"count": 0, "gm": ""}))
    campaign_games = defaultdict(lambda: defaultdict(lambda: {"count": 0, "gm": ""}))
    gm_names = []

    for session in sessions:
        game = session.game
        system = game.system.name
        game_name = game.name
        gm_name = game.gm.name

        if game.type == "oneshot":
            num_os += 1
            os_games[system][game_name]["count"] += 1
            os_games[system][game_name]["gm"] = gm_name
        else:
            num_campaign += 1
            campaign_games[system][game_name]["count"] += 1
            campaign_games[system][game_name]["gm"] = gm_name

        gm_names.append(gm_name)

    prev_month_date = base_day - relativedelta(months=1)
    next_month_date = base_day + relativedelta(months=1)

    return render_template(
        "stats.j2",
        payload=who(),
        base_day=base_day.strftime("%B %Y"),
        last_day=last_day.strftime("%a %d/%m"),
        num_os=num_os,
        num_campaign=num_campaign,
        os=os_games,
        campaign=campaign_games,
        mjs=Counter(gm_names),
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

    sessions = GameSession.query.filter(
        GameSession.start >= start, GameSession.end <= end
    ).all()

    events = []
    for session in sessions:
        events.append(
            {
                "id": session.id,
                "title": f"{session.game.name} par {session.game.gm.name}",
                "start": session.start.isoformat(),
                "end": session.end.isoformat(),
                "color": "#75b798" if session.game.type == "oneshot" else "#0d6efd",
                "url": url_for(GAME_DETAILS_ROUTE, slug=session.game.slug),
            }
        )

    return jsonify(events)
