from flask import (
    render_template,
)
from website import app
from website.models import Session
from website.views.auth import who
from datetime import datetime
from collections import Counter
import calendar


@app.route("/stats/", methods=["GET"])
def get_stats():
    """
    Get monthly statistics.
    """
    _, num_days = calendar.monthrange(datetime.today().year, datetime.today().month)
    base_day = datetime.today().replace(day=1, month=datetime.today().month - 1)
    last_day = datetime.today().replace(day=num_days, month=datetime.today().month - 1)
    monthly_sessions = Session.query.filter(Session.start >= base_day).filter(
        Session.end <= last_day
    )
    num_os = 0
    num_campaign = 0
    os = set()
    campaign = set()
    mjs = []
    for session in monthly_sessions:
        if session.game.type == "oneshot":
            num_os += 1
            os.add(session.game)
        else:
            num_campaign += 1
            campaign.add(session.game)
        mjs.append(session.game.gm.name)
    os_dict = {}
    campaign_dict = {}
    for i in os:
        if i.system.name not in os_dict:
            os_dict[i.system.name] = set()
        os_dict[i.system.name].add(i.name)
    for i in campaign:
        if i.system.name not in campaign_dict:
            campaign_dict[i.system.name] = set()
        campaign_dict[i.system.name].add(i.name)
    return render_template(
        "stats.html",
        payload=who(),
        base_day=base_day.strftime("%a %d/%m"),
        last_day=last_day.strftime("%a %d/%m"),
        num_os=num_os,
        num_campaign=num_campaign,
        os=os_dict,
        campaign=campaign_dict,
        mjs=Counter(mjs),
    )
