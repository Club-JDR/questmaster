"""Root test configuration.

Provides the Flask test app, transactional database sessions with
automatic rollback, and seeded reference data fixtures.
"""

from dotenv import load_dotenv

# Load env BEFORE importing app
config = load_dotenv()

import os

import pytest

from tests.constants import (
    TEST_ADMIN_USER_ID,
    TEST_CAMPAIGN_CHANNEL_ID,
    TEST_GM_USER_ID,
    TEST_ONESHOT_CHANNEL_ID,
    TEST_REGULAR_USER_ID,
)
from website import create_app, db
from website.client.discord import Discord
from website.extensions import _setup_test_database
from website.models import Channel, System, User, Vtt


@pytest.fixture(scope="module")
def test_app():
    """Create and configure the Flask test application."""
    app = create_app()
    with app.app_context():
        _setup_test_database()
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

    Reconfigures the *existing* ``db.session`` scoped_session rather than
    replacing it, so that module-level service singletons whose repositories
    captured a reference to ``db.session`` at import time transparently use
    the same transactional connection.
    """
    with test_app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()

        # Save original factory kwargs and reconfigure in-place so that
        # every reference to db.session (including those stored in repos)
        # uses the same connection with savepoint-based commit interception.
        original_kw = dict(db.session.session_factory.kw)
        db.session.remove()
        db.session.session_factory.kw.update(
            {"bind": connection, "join_transaction_mode": "create_savepoint"}
        )

        yield db.session

        db.session.remove()
        db.session.session_factory.kw = original_kw
        transaction.rollback()
        connection.close()


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
def gm_user(test_app):
    """Return the pre-seeded GM user (GM + player, not admin)."""
    return db.session.get(User, TEST_GM_USER_ID)


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
def logged_in_gm(test_app, gm_user):
    """Provide a Flask test client logged in as a GM (non-admin) user."""
    client = test_app.test_client()
    with client.session_transaction() as session:
        session["user_id"] = gm_user.id
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


@pytest.fixture(scope="module")
def test_channel_id(test_app):
    """Return the Discord test channel ID from the environment."""
    return os.environ.get("UNITTEST_CHANNEL_ID")
