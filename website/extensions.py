"""Flask extension instances and CLI commands."""

import click
from authlib.integrations.flask_client import OAuth
from flask.cli import with_appcontext
from flask_caching import Cache
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import inspect

db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
csrf = CSRFProtect()
oauth = OAuth()


def _is_db_initialized():
    inspector = inspect(db.engine)
    return "user" in inspector.get_table_names()


def _seed_test_data():
    """Seed the database with reference data for tests.

    Idempotent: each record is only inserted if it does not already exist, so
    re-seeding a non-empty database (e.g. after an interrupted run) is safe and
    does not raise duplicate-key errors.
    """
    from tests.constants import (
        TEST_ADMIN_USER_ID,
        TEST_ADMIN_USER_NAME,
        TEST_ADMIN_USER_USERNAME,
        TEST_CAMPAIGN_CHANNEL_ID,
        TEST_GM_USER_ID,
        TEST_GM_USER_NAME,
        TEST_GM_USER_USERNAME,
        TEST_ONESHOT_CHANNEL_ID,
        TEST_REGULAR_USER_ID,
        TEST_REGULAR_USER_NAME,
        TEST_REGULAR_USER_USERNAME,
        TEST_SPECIAL_EVENT_ID,
        TEST_SPECIAL_EVENT_NAME,
    )
    from website.models import Channel, SpecialEvent, System, User, Vtt

    users = [
        User(id=TEST_ADMIN_USER_ID, name=TEST_ADMIN_USER_NAME, username=TEST_ADMIN_USER_USERNAME),
        User(id=TEST_GM_USER_ID, name=TEST_GM_USER_NAME, username=TEST_GM_USER_USERNAME),
        User(
            id=TEST_REGULAR_USER_ID,
            name=TEST_REGULAR_USER_NAME,
            username=TEST_REGULAR_USER_USERNAME,
        ),
    ]
    for user in users:
        if db.session.get(User, user.id) is None:
            db.session.add(user)

    if db.session.query(System).filter_by(name="Appel de Cthulhu v7").first() is None:
        db.session.add(System(name="Appel de Cthulhu v7", icon="cthulhu.png"))
    if db.session.query(Vtt).filter_by(name="Foundry").first() is None:
        db.session.add(Vtt(name="Foundry", icon="foundry.png"))
    if db.session.get(Channel, TEST_ONESHOT_CHANNEL_ID) is None:
        db.session.add(Channel(id=TEST_ONESHOT_CHANNEL_ID, type="oneshot", size=20))
    if db.session.get(Channel, TEST_CAMPAIGN_CHANNEL_ID) is None:
        db.session.add(Channel(id=TEST_CAMPAIGN_CHANNEL_ID, type="campaign", size=20))
    if db.session.get(SpecialEvent, TEST_SPECIAL_EVENT_ID) is None:
        db.session.add(
            SpecialEvent(
                id=TEST_SPECIAL_EVENT_ID,
                name=TEST_SPECIAL_EVENT_NAME,
                emoji="\U0001f419",
                color=15360,
                active=True,
            )
        )
    db.session.commit()


def _setup_test_database():
    """Seed default trophy records into the database."""
    db.create_all()
    _seed_test_data()
    _seed_trophies()
    db.session.execute(db.text("SELECT setval('trophy_id_seq', 100, false);"))
    db.session.commit()


def _seed_trophies():
    """Seed default trophy records into the database."""
    from config.constants import (
        BADGE_CAMPAIGN_GM_ID,
        BADGE_CAMPAIGN_ID,
        BADGE_OS_GM_ID,
        BADGE_OS_ID,
    )
    from website.models.trophy import Trophy

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


@click.command("setup-test-db")
@with_appcontext
def setup_test_db():
    """CLI command to setup a test database."""
    if _is_db_initialized():
        click.echo("Database was already initialized.")
    else:
        _setup_test_database()
        click.echo("Database seeded with test data.")
