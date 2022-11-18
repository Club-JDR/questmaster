from dotenv import load_dotenv
from sqlalchemy import create_engine
import pytest
import os

# Load env BEFORE importing api
config = load_dotenv()
import api


@pytest.fixture()
def app():
    api.app.config["WTF_CSRF_METHODS"] = []  # disable CSRF for tests
    yield api.app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
