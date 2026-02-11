"""Unit tests for website.utils.game_embeds module.

Tests the Discord embed builder functions which return (embed_dict, channel_id) tuples.
Uses lightweight mock objects instead of real SQLAlchemy models since these are pure
formatting functions that only read attributes.
"""

from datetime import datetime
from types import SimpleNamespace

import pytest
from flask import Flask

from config.constants import (
    EMBED_COLOR_BLUE,
    EMBED_COLOR_DEFAULT,
    EMBED_COLOR_GREEN,
    EMBED_COLOR_RED,
    EMBED_COLOR_YELLOW,
    SITE_BASE_URL,
)
from website.utils.game_embeds import (
    _build_embed_fields,
    _build_embed_title,
    _build_restriction_message,
    _get_embed_color,
    _get_session_type,
    build_add_session_embed,
    build_alert_embed,
    build_annonce_details_embed,
    build_annonce_embed,
    build_delete_session_embed,
    build_edit_session_embed,
    build_register_embed,
)

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _make_game(**overrides):
    """Create a minimal game-like object with sensible defaults."""
    defaults = {
        "name": "Test Game",
        "slug": "test-game",
        "type": "oneshot",
        "status": "open",
        "restriction": "all",
        "restriction_tags": None,
        "date": datetime(2026, 3, 15, 14, 0),
        "length": "4h",
        "img": "https://example.com/img.png",
        "channel": "channel_123",
        "role": "role_456",
        "gm_id": "gm_789",
        "gm": SimpleNamespace(name="TestGM"),
        "system": SimpleNamespace(name="D&D 5e"),
        "special_event": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_special_event(**overrides):
    """Create a minimal special-event-like object."""
    defaults = {
        "name": "CthulhuFest",
        "emoji": "\U0001f419",
        "color": 15360,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


@pytest.fixture
def embed_app():
    """Minimal Flask app with config needed by embed builders."""
    app = Flask(__name__)
    app.config["POSTS_CHANNEL_ID"] = "test_posts_ch"
    app.config["ADMIN_CHANNEL_ID"] = "test_admin_ch"
    return app


# ---------------------------------------------------------------------------
# _build_restriction_message
# ---------------------------------------------------------------------------


class TestBuildRestrictionMessage:
    def test_all_restriction(self):
        game = _make_game(restriction="all")
        assert _build_restriction_message(game) == ":green_circle: Tout public"

    def test_16_plus_restriction(self):
        game = _make_game(restriction="16+")
        assert _build_restriction_message(game) == ":yellow_circle: 16+"

    def test_18_plus_restriction(self):
        game = _make_game(restriction="18+")
        assert _build_restriction_message(game) == ":red_circle: 18+"

    def test_unknown_restriction_defaults_to_18_plus(self):
        game = _make_game(restriction="unknown")
        assert _build_restriction_message(game) == ":red_circle: 18+"

    def test_restriction_with_tags(self):
        game = _make_game(restriction="16+", restriction_tags="violence, horreur")
        result = _build_restriction_message(game)
        assert result == ":yellow_circle: 16+ violence, horreur"

    def test_restriction_tags_none(self):
        game = _make_game(restriction="all", restriction_tags=None)
        result = _build_restriction_message(game)
        assert "Tout public" in result
        assert result.endswith("Tout public")


# ---------------------------------------------------------------------------
# _build_embed_title
# ---------------------------------------------------------------------------


class TestBuildEmbedTitle:
    def test_basic_title(self):
        game = _make_game(name="My Game", status="open")
        assert _build_embed_title(game) == "My Game"

    def test_closed_game_shows_complet(self):
        game = _make_game(name="My Game", status="closed")
        assert _build_embed_title(game) == "My Game (complet)"

    def test_special_event_with_emoji(self):
        event = _make_special_event(emoji="\U0001f419")
        game = _make_game(name="My Game", special_event=event)
        title = _build_embed_title(game)
        assert title == "\U0001f419 My Game \U0001f419"

    def test_special_event_without_emoji(self):
        event = _make_special_event(emoji=None)
        game = _make_game(name="My Game", special_event=event)
        assert _build_embed_title(game) == "My Game"

    def test_special_event_empty_emoji(self):
        event = _make_special_event(emoji="")
        game = _make_game(name="My Game", special_event=event)
        assert _build_embed_title(game) == "My Game"

    def test_closed_with_special_event(self):
        event = _make_special_event(emoji="\U0001f3b2")
        game = _make_game(name="Dice Night", status="closed", special_event=event)
        title = _build_embed_title(game)
        assert "(complet)" in title
        assert "\U0001f3b2" in title


# ---------------------------------------------------------------------------
# _get_session_type
# ---------------------------------------------------------------------------


class TestGetSessionType:
    def test_oneshot(self):
        game = _make_game(type="oneshot")
        assert _get_session_type(game) == "OS"

    def test_campaign(self):
        game = _make_game(type="campaign")
        assert _get_session_type(game) == "Campagne"

    def test_special_event_overrides_type(self):
        event = _make_special_event(name="CthulhuFest")
        game = _make_game(type="oneshot", special_event=event)
        assert _get_session_type(game) == "Événement spécial : CthulhuFest"


# ---------------------------------------------------------------------------
# _get_embed_color
# ---------------------------------------------------------------------------


class TestGetEmbedColor:
    def test_oneshot_color(self):
        game = _make_game(type="oneshot")
        assert _get_embed_color(game) == 0x198754

    def test_campaign_color(self):
        game = _make_game(type="campaign")
        assert _get_embed_color(game) == 0x0D6EFD

    def test_unknown_type_returns_default(self):
        game = _make_game(type="unknown")
        assert _get_embed_color(game) == EMBED_COLOR_DEFAULT

    def test_special_event_integer_color(self):
        event = _make_special_event(color=15360)
        game = _make_game(special_event=event)
        assert _get_embed_color(game) == 15360

    def test_special_event_hex_string_color(self):
        event = _make_special_event(color="#FF5733")
        game = _make_game(special_event=event)
        assert _get_embed_color(game) == 0xFF5733

    def test_special_event_hex_string_no_hash(self):
        event = _make_special_event(color="FF5733")
        game = _make_game(special_event=event)
        assert _get_embed_color(game) == 0xFF5733

    def test_special_event_invalid_hex_returns_default(self):
        event = _make_special_event(color="not-a-color")
        game = _make_game(special_event=event)
        assert _get_embed_color(game) == EMBED_COLOR_DEFAULT

    def test_special_event_none_color_uses_game_type(self):
        event = _make_special_event(color=None)
        game = _make_game(type="oneshot", special_event=event)
        assert _get_embed_color(game) == 0x198754


# ---------------------------------------------------------------------------
# _build_embed_fields
# ---------------------------------------------------------------------------


class TestBuildEmbedFields:
    def test_returns_seven_fields(self):
        game = _make_game()
        fields = _build_embed_fields(game, "OS", ":green_circle: Tout public")
        assert len(fields) == 7

    def test_field_names(self):
        game = _make_game()
        fields = _build_embed_fields(game, "OS", ":green_circle: Tout public")
        names = [f["name"] for f in fields]
        assert names == [
            "MJ",
            "Système",
            "Type de session",
            "Date",
            "Durée",
            "Avertissement",
            "Pour s'inscrire :",
        ]

    def test_gm_name_in_fields(self):
        game = _make_game(gm=SimpleNamespace(name="Alice"))
        fields = _build_embed_fields(game, "OS", "restriction")
        assert fields[0]["value"] == "Alice"

    def test_system_name_in_fields(self):
        game = _make_game(system=SimpleNamespace(name="Pathfinder"))
        fields = _build_embed_fields(game, "OS", "restriction")
        assert fields[1]["value"] == "Pathfinder"

    def test_session_type_in_fields(self):
        game = _make_game()
        fields = _build_embed_fields(game, "Campagne", "restriction")
        assert fields[2]["value"] == "Campagne"

    def test_game_url_in_fields(self):
        game = _make_game(slug="my-game")
        fields = _build_embed_fields(game, "OS", "restriction")
        assert f"{SITE_BASE_URL}/annonces/my-game/" in fields[6]["value"]

    def test_closed_game_strikethrough(self):
        game = _make_game(status="closed")
        fields = _build_embed_fields(game, "OS", "restriction")
        for field in fields:
            assert field["value"].startswith("~~")
            assert field["value"].endswith("~~")

    def test_open_game_no_strikethrough(self):
        game = _make_game(status="open")
        fields = _build_embed_fields(game, "OS", "restriction")
        for field in fields:
            assert not field["value"].startswith("~~")


# ---------------------------------------------------------------------------
# build_annonce_embed
# ---------------------------------------------------------------------------


class TestBuildAnnonceEmbed:
    def test_returns_tuple(self, embed_app):
        with embed_app.app_context():
            game = _make_game()
            result = build_annonce_embed(game)
            assert isinstance(result, tuple)
            assert len(result) == 2

    def test_embed_has_required_keys(self, embed_app):
        with embed_app.app_context():
            game = _make_game()
            embed, _ = build_annonce_embed(game)
            assert "title" in embed
            assert "color" in embed
            assert "fields" in embed
            assert "image" in embed
            assert "footer" in embed

    def test_channel_is_posts_channel(self, embed_app):
        with embed_app.app_context():
            game = _make_game()
            _, channel_id = build_annonce_embed(game)
            assert channel_id == "test_posts_ch"

    def test_image_url(self, embed_app):
        with embed_app.app_context():
            game = _make_game(img="https://example.com/image.png")
            embed, _ = build_annonce_embed(game)
            assert embed["image"]["url"] == "https://example.com/image.png"


# ---------------------------------------------------------------------------
# build_annonce_details_embed
# ---------------------------------------------------------------------------


class TestBuildAnnonceDetailsEmbed:
    def test_returns_tuple_with_game_channel(self):
        game = _make_game(channel="game_ch_123")
        _, channel_id = build_annonce_details_embed(game)
        assert channel_id == "game_ch_123"

    def test_embed_title(self):
        game = _make_game()
        embed, _ = build_annonce_details_embed(game)
        assert embed["title"] == "Tout est prêt."

    def test_embed_color_is_blue(self):
        game = _make_game()
        embed, _ = build_annonce_details_embed(game)
        assert embed["color"] == EMBED_COLOR_BLUE

    def test_description_contains_gm_mention(self):
        game = _make_game(gm_id="gm_999")
        embed, _ = build_annonce_details_embed(game)
        assert "<@gm_999>" in embed["description"]

    def test_description_contains_role_mention(self):
        game = _make_game(role="role_abc")
        embed, _ = build_annonce_details_embed(game)
        assert "<@&role_abc>" in embed["description"]

    def test_description_contains_game_url(self):
        game = _make_game(slug="my-slug")
        embed, _ = build_annonce_details_embed(game)
        assert f"{SITE_BASE_URL}/annonces/my-slug" in embed["description"]


# ---------------------------------------------------------------------------
# build_add_session_embed
# ---------------------------------------------------------------------------


class TestBuildAddSessionEmbed:
    def test_returns_game_channel(self):
        game = _make_game(channel="ch_add")
        _, channel_id = build_add_session_embed(
            game, start="lun 01/01", end="lun 01/01"
        )
        assert channel_id == "ch_add"

    def test_embed_color_is_green(self):
        game = _make_game()
        embed, _ = build_add_session_embed(game, start="start", end="end")
        assert embed["color"] == EMBED_COLOR_GREEN

    def test_description_contains_dates(self):
        game = _make_game()
        embed, _ = build_add_session_embed(game, start="lun 01/01", end="mar 02/01")
        assert "lun 01/01" in embed["description"]
        assert "mar 02/01" in embed["description"]

    def test_description_contains_role_mention(self):
        game = _make_game(role="role_x")
        embed, _ = build_add_session_embed(game, start="s", end="e")
        assert "<@&role_x>" in embed["description"]


# ---------------------------------------------------------------------------
# build_edit_session_embed
# ---------------------------------------------------------------------------


class TestBuildEditSessionEmbed:
    def test_returns_game_channel(self):
        game = _make_game(channel="ch_edit")
        _, channel_id = build_edit_session_embed(game, start="new", old_start="old")
        assert channel_id == "ch_edit"

    def test_embed_color_is_yellow(self):
        game = _make_game()
        embed, _ = build_edit_session_embed(game, start="new", old_start="old")
        assert embed["color"] == EMBED_COLOR_YELLOW

    def test_description_contains_old_and_new(self):
        game = _make_game()
        embed, _ = build_edit_session_embed(
            game, start="mar 05/03", old_start="lun 04/03"
        )
        assert "mar 05/03" in embed["description"]
        assert "lun 04/03" in embed["description"]

    def test_old_start_has_strikethrough(self):
        game = _make_game()
        embed, _ = build_edit_session_embed(game, start="new", old_start="old_date")
        assert "~~du old_date~~" in embed["description"]


# ---------------------------------------------------------------------------
# build_delete_session_embed
# ---------------------------------------------------------------------------


class TestBuildDeleteSessionEmbed:
    def test_returns_game_channel(self):
        game = _make_game(channel="ch_del")
        _, channel_id = build_delete_session_embed(game, start="s", end="e")
        assert channel_id == "ch_del"

    def test_embed_color_is_red(self):
        game = _make_game()
        embed, _ = build_delete_session_embed(game, start="s", end="e")
        assert embed["color"] == EMBED_COLOR_RED

    def test_description_contains_dates(self):
        game = _make_game()
        embed, _ = build_delete_session_embed(game, start="lun 01/01", end="mar 02/01")
        assert "lun 01/01" in embed["description"]
        assert "mar 02/01" in embed["description"]


# ---------------------------------------------------------------------------
# build_register_embed
# ---------------------------------------------------------------------------


class TestBuildRegisterEmbed:
    def test_returns_game_channel(self):
        game = _make_game(channel="ch_reg")
        _, channel_id = build_register_embed(game, player="player_1")
        assert channel_id == "ch_reg"

    def test_embed_color_is_blue(self):
        game = _make_game()
        embed, _ = build_register_embed(game, player="player_1")
        assert embed["color"] == EMBED_COLOR_BLUE

    def test_description_contains_player_mention(self):
        game = _make_game()
        embed, _ = build_register_embed(game, player="player_42")
        assert "<@player_42>" in embed["description"]

    def test_description_contains_welcome(self):
        game = _make_game()
        embed, _ = build_register_embed(game, player="p")
        assert ":wave:" in embed["description"]


# ---------------------------------------------------------------------------
# build_alert_embed
# ---------------------------------------------------------------------------


class TestBuildAlertEmbed:
    def test_returns_admin_channel(self, embed_app):
        with embed_app.app_context():
            game = _make_game()
            _, channel_id = build_alert_embed(game, player="p", alert_message="msg")
            assert channel_id == "test_admin_ch"

    def test_embed_color_is_red(self, embed_app):
        with embed_app.app_context():
            game = _make_game()
            embed, _ = build_alert_embed(game, player="p", alert_message="msg")
            assert embed["color"] == EMBED_COLOR_RED

    def test_description_contains_player_and_message(self, embed_app):
        with embed_app.app_context():
            game = _make_game()
            embed, _ = build_alert_embed(
                game, player="player_99", alert_message="Bad behavior"
            )
            assert "<@player_99>" in embed["description"]
            assert "Bad behavior" in embed["description"]

    def test_description_contains_channel_link(self, embed_app):
        with embed_app.app_context():
            game = _make_game(channel="game_ch_100")
            embed, _ = build_alert_embed(game, player="p", alert_message="msg")
            assert "<#game_ch_100>" in embed["description"]

    def test_description_contains_game_url(self, embed_app):
        with embed_app.app_context():
            game = _make_game(slug="alert-game")
            embed, _ = build_alert_embed(game, player="p", alert_message="msg")
            assert f"{SITE_BASE_URL}/annonces/alert-game" in embed["description"]
