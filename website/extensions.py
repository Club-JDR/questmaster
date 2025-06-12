from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect
from flask_discord import DiscordOAuth2Session
from flask.cli import with_appcontext
import click



db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
csrf = CSRFProtect()
discord = DiscordOAuth2Session()


@click.command("seed-trophies")
@with_appcontext
def seed_trophies():
    from website.models.trophy import (
        Trophy,
        BADGE_OS_ID,
        BADGE_OS_GM_ID,
        BADGE_CAMPAIGN_ID,
        BADGE_CAMPAIGN_GM_ID,
    )

    trophies_to_ensure = [
        {
            "id": BADGE_OS_ID,
            "name": "Badge OS",
            "unique": False,
            "icon": "/static/img/os.png",
        },
        {
            "id": BADGE_OS_GM_ID,
            "name": "Badge OS GM",
            "unique": False,
            "icon": "/static/img/os_gm.png",
        },
        {
            "id": BADGE_CAMPAIGN_ID,
            "name": "Badge Campagne",
            "unique": False,
            "icon": "/static/img/campaign.png",
        },
        {
            "id": BADGE_CAMPAIGN_GM_ID,
            "name": "Badge Campagne GM",
            "unique": False,
            "icon": "/static/img/campaign_gm.png",
        },
    ]

    for trophy_data in trophies_to_ensure:
        trophy = db.session.get(Trophy, trophy_data["id"])
        if not trophy:
            new_trophy = Trophy(**trophy_data)
            db.session.add(new_trophy)

    db.session.commit()
