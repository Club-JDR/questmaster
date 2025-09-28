from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect
from flask_discord import DiscordOAuth2Session
from flask.cli import with_appcontext
from flask import current_app
import click, requests, re, time


db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
csrf = CSRFProtect()
discord = DiscordOAuth2Session()


def _sync_badges_to_db(user_badges_map):
    from website.models import User, UserTrophy
    from website.models.trophy import (
        BADGE_OS_ID,
        BADGE_OS_GM_ID,
        BADGE_CAMPAIGN_ID,
        BADGE_CAMPAIGN_GM_ID,
    )

    BADGE_MAP = {
        "db76e19d3a": BADGE_OS_ID,
        "3c32619517": BADGE_OS_GM_ID,
        "bbcaf7cd82": BADGE_OS_GM_ID,
        "6ddf78bd34": BADGE_CAMPAIGN_ID,
        "668a07d3d6": BADGE_CAMPAIGN_GM_ID,
        "f0e67fc78e": 7,
        "a5fc074a70": 6,
        "14b5cea376": 5,
        "f6186828b6": 7,
    }

    for user_id, badges in user_badges_map.items():
        user_id_str = str(user_id)  # User.id is a String

        # ensure user exists
        user = db.session.get(User, user_id_str)
        if not user:
            user = User(id=user_id_str, name="Inconnu")
            db.session.add(user)

        # process each badge for this user
        for badge_code, count in badges.items():
            if badge_code not in BADGE_MAP:
                current_app.logger.warning(f"Unknown badge code {badge_code}, skipping.")
                continue

            trophy_id = BADGE_MAP[badge_code]

            # check if user already has this trophy
            ut = (
                db.session.query(UserTrophy)
                .filter_by(user_id=user_id_str, trophy_id=trophy_id)
                .first()
            )

            if ut:
                if ut.trophy_id == 5 or ut.trophy_id == 6:
                    ut.quantity = count # should be 1
                else:
                    ut.quantity += count  # ✅ increment
            else:
                ut = UserTrophy(user_id=user_id_str, trophy_id=trophy_id, quantity=count)
                db.session.add(ut)
            click.echo(f"User {user_id} will now have {count} badges {ut.trophy_id}.")

    db.session.commit()
    click.echo("✅ Incrementally synced users and trophies to DB.")


def _parse_channel():
    CHANNEL_ID = "1413591303156924476"
    BASE_URL = "https://discord.com/api/v10"

    headers = {"Authorization": f"Bot {current_app.config['DISCORD_BOT_TOKEN']}"}
    url = f"{BASE_URL}/channels/{CHANNEL_ID}/messages"
    params = {"limit": 100}

    all_messages = []
    last_id = None
    user_badges_map = {}

    while True:
        if last_id:
            params["before"] = last_id

        resp = requests.get(url, headers=headers, params=params)
        time.sleep(1)

        if resp.status_code != 200:
            click.echo(f"Error: {resp.status_code} {resp.text}")
            break

        messages = resp.json()
        if not messages:
            break

        for msg in messages:
            if not msg.get("embeds"):
                continue
            s = msg["embeds"][0].get("description")
            if not s:
                continue

            # extract user id
            user_id_match = re.search(r"<@!?(\d+)>", s)
            user_id = int(user_id_match.group(1)) if user_id_match else None

            # extract badges
            badge_pattern = re.compile(r"`([a-f0-9]+)`\s*-\s*\(x(\d+)\)")
            badges = {code: int(count) for code, count in badge_pattern.findall(s)}

            if user_id:
                if user_id not in user_badges_map:
                    user_badges_map[user_id] = badges
                else:
                    # merge counts across multiple messages
                    for code, count in badges.items():
                        user_badges_map[user_id][code] = (
                            user_badges_map[user_id].get(code, 0) + count
                        )

        all_messages.extend(messages)
        last_id = messages[-1]["id"]

    click.echo(f"✅ Fetched {len(all_messages)} messages in total.")
    _sync_badges_to_db(user_badges_map)



def _seed_trophies():
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


@click.command("seed-trophies")
@with_appcontext
def seed_trophies():
    """CLI command to seed trophies."""
    _seed_trophies()


@click.command("parse-messages")
@with_appcontext
def parse_messages():
    _parse_channel()


def seed_trophies_for_tests():
    """Call this function in tests to seed trophies."""
    _seed_trophies()
