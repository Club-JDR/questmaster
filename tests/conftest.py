"""Root test configuration.

Provides the Flask test app, transactional database sessions with
automatic rollback, and seeded reference data fixtures.
"""

from dotenv import load_dotenv

# Load env BEFORE importing app
config = load_dotenv()

import os

import pytest
from sqlalchemy.orm import scoped_session, sessionmaker

from website import create_app, db
from website.client.discord import Discord
from website.extensions import seed_trophies_for_tests
from website.models import Channel, SpecialEvent, System, User, Vtt

from tests.constants import (
    TEST_ADMIN_USER_ID,
    TEST_ADMIN_USER_NAME,
    TEST_CAMPAIGN_CHANNEL_ID,
    TEST_ONESHOT_CHANNEL_ID,
    TEST_REGULAR_USER_ID,
    TEST_REGULAR_USER_NAME,
    TEST_SPECIAL_EVENT_ID,
    TEST_SPECIAL_EVENT_NAME,
)


def seed_db():
    """Seed the database with reference data for tests."""
    db.session.add_all(
        [
            User(id=TEST_ADMIN_USER_ID, name=TEST_ADMIN_USER_NAME),
            User(id=TEST_REGULAR_USER_ID, name=TEST_REGULAR_USER_NAME),
        ]
    )
    db.session.add(System(name="Appel de Cthulhu v7", icon="cthulhu.png"))
    db.session.add(Vtt(name="Foundry", icon="foundry.png"))
    db.session.add(Channel(id=TEST_ONESHOT_CHANNEL_ID, type="oneshot", size=20))
    db.session.add(Channel(id=TEST_CAMPAIGN_CHANNEL_ID, type="campaign", size=20))
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


@pytest.fixture(scope="module")
def test_app():
    """Create and configure the Flask test application."""
    app = create_app()
    with app.app_context():
        db.create_all()
        seed_db()
        seed_trophies_for_tests()
        # Reset Trophy sequence to avoid ID conflicts (seeded trophies use IDs 1-4)
        db.session.execute(db.text("SELECT setval('trophy_id_seq', 100, false);"))
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def db_session(test_app):
    """Provide a transactional database session that rolls back after each test.

    Uses nested transactions (savepoints) so that even service-layer code
    calling ``db.session.commit()`` writes to a savepoint rather than the
    real transaction.  The outer transaction is rolled back in teardown,
    leaving the database unchanged between tests.
    """
    with test_app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        # Build a new session factory that preserves Flask-SQLAlchemy's
        # Session class and kwargs (db, query_cls, etc.) while binding
        # to our connection with savepoint-based commit interception.
        original_factory = db.session.session_factory
        new_kw = dict(original_factory.kw)
        new_kw["bind"] = connection
        new_kw["join_transaction_mode"] = "create_savepoint"
        factory = sessionmaker(class_=original_factory.class_, **new_kw)
        session = scoped_session(factory)
        original_session = db.session
        db.session = session

        yield session

        session.remove()
        transaction.rollback()
        connection.close()
        db.session = original_session


@pytest.fixture(scope="module")
def discord_session():
    """Provide a Discord API client (requires live credentials)."""
    return Discord(os.getenv("DISCORD_GUILD_ID"), os.getenv("DISCORD_BOT_TOKEN"))


@pytest.fixture
def client(test_app):
    """Provide a Flask test client."""
    return test_app.test_client()


@pytest.fixture
def regular_user(test_app):
    """Return the pre-seeded regular user."""
    return db.session.get(User, TEST_REGULAR_USER_ID)


@pytest.fixture
def admin_user(test_app):
    """Return the pre-seeded admin user."""
    return db.session.get(User, TEST_ADMIN_USER_ID)


@pytest.fixture
def default_system(test_app):
    """Return the pre-seeded RPG system."""
    return System.query.first()


@pytest.fixture
def default_vtt(test_app):
    """Return the pre-seeded VTT."""
    return Vtt.query.first()


@pytest.fixture
def oneshot_channel(test_app):
    """Return the pre-seeded one-shot channel."""
    return db.session.get(Channel, TEST_ONESHOT_CHANNEL_ID)


@pytest.fixture
def campaign_channel(test_app):
    """Return the pre-seeded campaign channel."""
    return db.session.get(Channel, TEST_CAMPAIGN_CHANNEL_ID)


@pytest.fixture
def logged_in_admin(test_app, admin_user):
    """Provide a Flask test client logged in as the admin user."""
    client = test_app.test_client()
    with client.session_transaction() as session:
        session["user_id"] = admin_user.id
    return client


@pytest.fixture
def logged_in_user(test_app, regular_user):
    """Provide a Flask test client logged in as a regular user."""
    client = test_app.test_client()
    with client.session_transaction() as session:
        session["user_id"] = regular_user.id
    return client


@pytest.fixture
def bot_user_id(test_app):
    """Return the Discord bot client ID from the environment."""
    return os.environ.get("DISCORD_CLIENT_ID")


@pytest.fixture
def test_channel_id(test_app):
    """Return the Discord test channel ID from the environment."""
    return os.environ.get("UNITTEST_CHANNEL_ID")
