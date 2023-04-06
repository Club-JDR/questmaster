from dotenv import load_dotenv
import pytest

# Load env BEFORE importing app
config = load_dotenv()
import website


@pytest.fixture()
def app():
    website.app.config["WTF_CSRF_METHODS"] = []  # disable CSRF for tests
    yield website.app


@pytest.fixture()
def client(app):
    return app.test_client()
