"""Shared fixtures for utility tests."""

import pytest
from flask import Flask


@pytest.fixture
def parser_app():
    """Minimal Flask app for request-context-dependent parsers."""
    return Flask(__name__)


@pytest.fixture
def embed_app():
    """Minimal Flask app with config needed by embed builders."""
    app = Flask(__name__)
    app.config["POSTS_CHANNEL_ID"] = "test_posts_ch"
    app.config["ADMIN_CHANNEL_ID"] = "test_admin_ch"
    return app
