from dotenv import load_dotenv

# Load env BEFORE importing app
config = load_dotenv()
from website import create_app, db
from website.models import User, System, Vtt, Channel
from website.utils.discord import Discord
from website.extensions import seed_trophies_for_tests
from flask import template_rendered
from contextlib import contextmanager
import pytest, os


def seed_db():
    db.session.add_all(
        [
            User(id="664487064577900594", name="Notsag"),
            User(id="698965618279317624", name="Grew"),
        ]
    )
    db.session.add(System(name="Appel de Cthulhu v7", icon="cthulhu.png"))
    db.session.add(Vtt(name="Foundry", icon="foundry.png"))
    db.session.add(Channel(id="1247613267552108696", type="oneshot", size=20))
    db.session.add(Channel(id="1247613296870162474", type="campaign", size=20))
    db.session.commit()


@pytest.fixture(scope="module")
def test_app():
    app = create_app()
    with app.app_context():
        db.create_all()
        seed_db()
        seed_trophies_for_tests()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def db_session(test_app):
    with test_app.app_context():
        yield db.session


@pytest.fixture(scope="module")
def discord_session():
    return Discord(os.getenv("DISCORD_GUILD_ID"), os.getenv("DISCORD_BOT_TOKEN"))


@pytest.fixture
def client(test_app):
    return test_app.test_client()


@pytest.fixture
def regular_user(test_app):
    return db.session.get(User, "698965618279317624")


@pytest.fixture
def admin_user(test_app):
    return db.session.get(User, "664487064577900594")


@pytest.fixture
def default_system(test_app):
    return System.query.first()


@pytest.fixture
def default_vtt(test_app):
    return Vtt.query.first()


@pytest.fixture
def oneshot_channel(test_app):
    return db.session.get(Channel, "1247613267552108696")


@pytest.fixture
def campaign_channel(test_app):
    return db.session.get(Channel, "1247613296870162474")


@pytest.fixture
def bot_user_id(test_app):
    return os.environ.get("DISCORD_CLIENT_ID")


@pytest.fixture
def test_channel_id(test_app):
    return os.environ.get("UNITTEST_CHANNEL_ID")
