from dotenv import load_dotenv
import pytest

config = load_dotenv()

import api


@pytest.fixture()
def app():
    yield api.app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
