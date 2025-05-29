from flask import render_template, Blueprint
from website.models import GameSession
from website.views.auth import who
from datetime import datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict, Counter
import calendar

stats_bp = Blueprint("stats", __name__)


@stats_bp.route("/stats/", methods=["GET"])
def get_stats():
    """
    Get monthly statistics for sessions, grouped by type and system.
    """
    today = datetime.today()
    base_day = today.replace(day=1) - relativedelta(months=1)
    last_day = base_day.replace(
        day=calendar.monthrange(base_day.year, base_day.month)[1]
    )

    # Query all sessions in the previous month
    sessions = GameSession.query.filter(
        GameSession.start >= base_day,
        GameSession.end <= last_day
    ).all()

    num_os = 0
    num_campaign = 0
    os_games = set()
    campaign_games = set()
    gm_names = []

    for session in sessions:
        game = session.game
        if game.type == "oneshot":
            num_os += 1
            os_games.add(game)
        else:
            num_campaign += 1
            campaign_games.add(game)
        gm_names.append(game.gm.name)

    # Group games by system
    def group_games_by_system(games):
        grouped = defaultdict(set)
        for game in games:
            grouped[game.system.name].add(game.name)
        return grouped

    os_dict = group_games_by_system(os_games)
    campaign_dict = group_games_by_system(campaign_games)

    return render_template(
        "stats.html",
        payload=who(),
        base_day=base_day.strftime("%a %d/%m"),
        last_day=last_day.strftime("%a %d/%m"),
        num_os=num_os,
        num_campaign=num_campaign,
        os=os_dict,
        campaign=campaign_dict,
        mjs=Counter(gm_names),
    )
