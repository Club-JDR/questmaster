"""Tests for the Discord HTTP-interactions endpoint."""

import json
from unittest.mock import patch
from uuid import uuid4

import pytest
from nacl.signing import SigningKey

from tests.factories import GameFactory

ENDPOINT = "/discord/interactions"
TIMESTAMP = "1700000000"


@pytest.fixture
def signing_key(test_app):
    """Generate an Ed25519 key pair and configure its public key on the app."""
    key = SigningKey.generate()
    previous = test_app.config.get("DISCORD_PUBLIC_KEY")
    test_app.config["DISCORD_PUBLIC_KEY"] = key.verify_key.encode().hex()
    yield key
    test_app.config["DISCORD_PUBLIC_KEY"] = previous


def _post_signed(client, key, payload):
    """POST a payload signed with ``key`` the way Discord signs interactions."""
    body = json.dumps(payload).encode()
    signature = key.sign(TIMESTAMP.encode() + body).signature.hex()
    return client.post(
        ENDPOINT,
        data=body,
        headers={
            "X-Signature-Ed25519": signature,
            "X-Signature-Timestamp": TIMESTAMP,
            "Content-Type": "application/json",
        },
    )


class TestSignatureVerification:
    def test_ping_with_valid_signature_returns_pong(self, client, signing_key):
        response = _post_signed(client, signing_key, {"type": 1})
        assert response.status_code == 200
        assert response.get_json() == {"type": 1}

    def test_wrong_key_signature_returns_401(self, client, signing_key):
        wrong_key = SigningKey.generate()
        response = _post_signed(client, wrong_key, {"type": 1})
        assert response.status_code == 401

    def test_missing_signature_headers_returns_401(self, client, signing_key):
        response = client.post(
            ENDPOINT, data=b'{"type": 1}', headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 401

    def test_unconfigured_public_key_returns_401(self, client, test_app):
        test_app.config["DISCORD_PUBLIC_KEY"] = None
        key = SigningKey.generate()
        response = _post_signed(client, key, {"type": 1})
        assert response.status_code == 401


class TestCommandDispatch:
    def test_info_command_answers_inline(self, client, signing_key, db_session):
        game = GameFactory(
            db_session,
            status="open",
            channel=str(uuid4().int)[:18],
        )
        payload = {
            "type": 2,
            "token": "tok",
            "channel_id": game.channel,
            "data": {"name": "info"},
        }

        response = _post_signed(client, signing_key, payload)

        assert response.status_code == 200
        data = response.get_json()
        assert data["type"] == 4
        assert data["data"]["flags"] == 64
        assert game.name in data["data"]["content"]

    def test_mutating_command_defers_and_dispatches_async(self, client, signing_key):
        payload = {
            "type": 2,
            "token": "tok",
            "channel_id": "000000000000000000",
            "member": {"user": {"id": "42", "username": "tester"}},
            "data": {"name": "signaler", "options": [{"name": "message", "value": "x"}]},
        }

        with patch(
            "website.views.discord_interactions.command_service.dispatch_async"
        ) as dispatch:
            response = _post_signed(client, signing_key, payload)

        assert response.status_code == 200
        data = response.get_json()
        assert data["type"] == 5
        assert data["data"]["flags"] == 64
        dispatch.assert_called_once()

    def test_unknown_interaction_type_returns_pong(self, client, signing_key):
        response = _post_signed(client, signing_key, {"type": 99})
        assert response.status_code == 200
        assert response.get_json() == {"type": 1}


class TestHelpPage:
    def test_discord_commands_help_page_renders(self, client, db_session):
        response = client.get("/aide/commandes-discord/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "Commandes Discord" in body
        for command in ("/info", "/signaler", "/notifier", "/ajouter-session"):
            assert command in body
