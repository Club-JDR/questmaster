"""Unit tests for website.utils.game_filters module.

Tests filter-building functions in isolation (pure logic and SQLAlchemy
filter construction) and integration tests for the paginated query helpers.
"""

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest
from werkzeug.datastructures import MultiDict

from config.constants import (
    GAME_STATUS_DRAFT,
    GAME_STATUS_OPEN,
    GAME_STATUS_CLOSED,
    GAME_STATUS_ARCHIVED,
    GAME_TYPE_ONESHOT,
    GAME_TYPE_CAMPAIGN,
    GAMES_PER_PAGE,
)
from website.exceptions import ValidationError
from website.models import Game, System, Vtt, User
from website.utils.game_filters import (
    build_base_filters,
    build_status_filters,
    get_filtered_games,
    get_filtered_user_games,
    normalize_search_defaults,
    parse_multi_checkbox_filter,
)

from tests.constants import TEST_ADMIN_USER_ID, TEST_REGULAR_USER_ID


# ---------------------------------------------------------------------------
# parse_multi_checkbox_filter
# ---------------------------------------------------------------------------


class TestParseMultiCheckboxFilter:
    def test_all_selected(self):
        source = MultiDict({"open": "on", "closed": "on"})
        filters, args = parse_multi_checkbox_filter(source, ["open", "closed"])
        assert filters == ["open", "closed"]
        assert args == {"open": "on", "closed": "on"}

    def test_none_selected(self):
        source = MultiDict({})
        filters, args = parse_multi_checkbox_filter(source, ["open", "closed"])
        assert filters == []
        assert args == {}

    def test_partial_selection(self):
        source = MultiDict({"closed": "on"})
        filters, args = parse_multi_checkbox_filter(
            source, ["open", "closed", "archived"]
        )
        assert filters == ["closed"]
        assert args == {"closed": "on"}

    def test_unrelated_keys_ignored(self):
        source = MultiDict({"open": "on", "unrelated": "on"})
        filters, args = parse_multi_checkbox_filter(source, ["open", "closed"])
        assert filters == ["open"]
        assert args == {"open": "on"}


# ---------------------------------------------------------------------------
# build_base_filters
# ---------------------------------------------------------------------------


class TestBuildBaseFilters:
    def test_no_filters(self):
        request_args = {}
        filters = build_base_filters(request_args, None, None, None)
        assert filters == []
        assert request_args == {}

    def test_name_filter(self):
        request_args = {}
        filters = build_base_filters(request_args, "Cthulhu", None, None)
        assert len(filters) == 1
        assert request_args == {"name": "Cthulhu"}

    def test_system_filter(self):
        request_args = {}
        filters = build_base_filters(request_args, None, 5, None)
        assert len(filters) == 1
        assert request_args == {"system": 5}

    def test_vtt_filter(self):
        request_args = {}
        filters = build_base_filters(request_args, None, None, 3)
        assert len(filters) == 1
        assert request_args == {"vtt": 3}

    def test_all_filters(self):
        request_args = {}
        filters = build_base_filters(request_args, "test", 1, 2)
        assert len(filters) == 3
        assert request_args == {"name": "test", "system": 1, "vtt": 2}


# ---------------------------------------------------------------------------
# build_status_filters
# ---------------------------------------------------------------------------


class TestBuildStatusFilters:
    def test_non_draft_status(self):
        user_payload = {"user_id": "123", "is_admin": False}
        result = build_status_filters(["open"], user_payload)
        assert result is not None

    def test_draft_for_admin(self):
        user_payload = {"user_id": "123", "is_admin": True}
        result = build_status_filters(["draft"], user_payload)
        assert result is not None

    def test_draft_for_non_admin(self):
        user_payload = {"user_id": "123", "is_admin": False}
        result = build_status_filters(["draft"], user_payload)
        assert result is not None

    def test_multiple_statuses(self):
        user_payload = {"user_id": "123", "is_admin": False}
        result = build_status_filters(["open", "closed", "draft"], user_payload)
        assert result is not None


# ---------------------------------------------------------------------------
# normalize_search_defaults
# ---------------------------------------------------------------------------


class TestNormalizeSearchDefaults:
    def test_empty_inputs_use_defaults(self):
        status, game_type, restriction = normalize_search_defaults([], [], [])
        assert status == ["open"]
        assert game_type == ["oneshot", "campaign"]
        assert restriction == ["all", "16+", "18+"]

    def test_provided_values_kept(self):
        status, game_type, restriction = normalize_search_defaults(
            ["closed"], ["oneshot"], ["16+"]
        )
        assert status == ["closed"]
        assert game_type == ["oneshot"]
        assert restriction == ["16+"]

    def test_custom_defaults(self):
        status, game_type, restriction = normalize_search_defaults(
            [],
            [],
            [],
            default_status=["draft", "open"],
            default_type=["campaign"],
            default_restriction=["all"],
        )
        assert status == ["draft", "open"]
        assert game_type == ["campaign"]
        assert restriction == ["all"]

    def test_partial_empty(self):
        status, game_type, restriction = normalize_search_defaults(
            ["open", "closed"], [], ["all"]
        )
        assert status == ["open", "closed"]
        assert game_type == ["oneshot", "campaign"]
        assert restriction == ["all"]

    def test_none_defaults_use_builtin(self):
        status, game_type, restriction = normalize_search_defaults(
            [], [], [], default_status=None, default_type=None, default_restriction=None
        )
        assert status == ["open"]
        assert game_type == ["oneshot", "campaign"]
        assert restriction == ["all", "16+", "18+"]


# ---------------------------------------------------------------------------
# get_filtered_games (integration — requires db_session)
# ---------------------------------------------------------------------------


def _create_game(db_session, admin_user, default_system, default_vtt, **overrides):
    """Helper to create a game in the database."""
    from uuid import uuid4

    uid = uuid4().hex[:8]
    defaults = {
        "name": f"Filter Test Game {uid}",
        "slug": f"filter-test-{uid}",
        "type": GAME_TYPE_ONESHOT,
        "status": GAME_STATUS_OPEN,
        "system_id": default_system.id,
        "vtt_id": default_vtt.id,
        "gm_id": admin_user.id,
        "party_size": 4,
        "length": "4h",
        "description": "A test game for filters",
        "restriction": "all",
        "date": datetime(2026, 6, 15, 14, 0),
        "session_length": Decimal("3.0"),
        "img": "https://example.com/img.png",
    }
    defaults.update(overrides)
    game = Game(**defaults)
    db_session.add(game)
    db_session.flush()
    return game


class TestGetFilteredGames:
    def test_returns_pagination_and_args(
        self, db_session, admin_user, default_system, default_vtt
    ):
        _create_game(db_session, admin_user, default_system, default_vtt)
        source = MultiDict({})
        user_payload = {"user_id": TEST_ADMIN_USER_ID, "is_admin": True}
        games, request_args = get_filtered_games(source, user_payload)
        assert hasattr(games, "items")
        assert isinstance(request_args, dict)

    def test_filters_by_status(
        self, db_session, admin_user, default_system, default_vtt
    ):
        _create_game(
            db_session,
            admin_user,
            default_system,
            default_vtt,
            status=GAME_STATUS_CLOSED,
            name="Closed Filter Game",
        )
        source = MultiDict({"closed": "on"})
        user_payload = {"user_id": TEST_ADMIN_USER_ID, "is_admin": True}
        games, _ = get_filtered_games(source, user_payload)
        statuses = [g.status for g in games.items]
        assert all(s == GAME_STATUS_CLOSED for s in statuses)

    def test_filters_by_game_type(
        self, db_session, admin_user, default_system, default_vtt
    ):
        _create_game(
            db_session,
            admin_user,
            default_system,
            default_vtt,
            type=GAME_TYPE_CAMPAIGN,
            status=GAME_STATUS_OPEN,
            name="Campaign Filter Game",
        )
        source = MultiDict({"open": "on", "campaign": "on"})
        user_payload = {"user_id": TEST_ADMIN_USER_ID, "is_admin": True}
        games, _ = get_filtered_games(source, user_payload)
        types = [g.type for g in games.items]
        assert all(t == GAME_TYPE_CAMPAIGN for t in types)

    def test_filters_by_name(self, db_session, admin_user, default_system, default_vtt):
        _create_game(
            db_session,
            admin_user,
            default_system,
            default_vtt,
            name="UniqueNameXYZ789",
            status=GAME_STATUS_OPEN,
        )
        source = MultiDict({"open": "on", "name": "UniqueNameXYZ789"})
        user_payload = {"user_id": TEST_ADMIN_USER_ID, "is_admin": True}
        games, request_args = get_filtered_games(source, user_payload)
        assert any(g.name == "UniqueNameXYZ789" for g in games.items)
        assert request_args["name"] == "UniqueNameXYZ789"

    def test_draft_visible_to_own_gm(
        self, db_session, admin_user, default_system, default_vtt
    ):
        _create_game(
            db_session,
            admin_user,
            default_system,
            default_vtt,
            status=GAME_STATUS_DRAFT,
            name="My Draft Game",
        )
        source = MultiDict({"draft": "on"})
        user_payload = {"user_id": TEST_ADMIN_USER_ID, "is_admin": False}
        games, _ = get_filtered_games(source, user_payload)
        assert any(g.name == "My Draft Game" for g in games.items)

    def test_pagination_respects_page_param(
        self, db_session, admin_user, default_system, default_vtt
    ):
        source = MultiDict({"page": "1"})
        user_payload = {"user_id": TEST_ADMIN_USER_ID, "is_admin": True}
        games, _ = get_filtered_games(source, user_payload)
        assert games.page == 1

    def test_default_status_override(
        self, db_session, admin_user, default_system, default_vtt
    ):
        _create_game(
            db_session,
            admin_user,
            default_system,
            default_vtt,
            status=GAME_STATUS_ARCHIVED,
            name="Archived Default Game",
        )
        source = MultiDict({})
        user_payload = {"user_id": TEST_ADMIN_USER_ID, "is_admin": True}
        games, _ = get_filtered_games(source, user_payload, default_status=["archived"])
        statuses = [g.status for g in games.items]
        assert all(s == GAME_STATUS_ARCHIVED for s in statuses)


# ---------------------------------------------------------------------------
# get_filtered_user_games (integration — requires db_session)
# ---------------------------------------------------------------------------


class TestGetFilteredUserGames:
    def test_gm_role_returns_games_as_gm(
        self, db_session, admin_user, default_system, default_vtt
    ):
        _create_game(
            db_session,
            admin_user,
            default_system,
            default_vtt,
            name="GM User Game",
            status=GAME_STATUS_OPEN,
        )
        source = MultiDict({"open": "on"})
        user_payload = {"user_id": TEST_ADMIN_USER_ID, "is_admin": True}
        games, _ = get_filtered_user_games(
            source, TEST_ADMIN_USER_ID, user_payload, role="gm"
        )
        assert hasattr(games, "items")
        gm_ids = [g.gm_id for g in games.items]
        assert all(gm_id == TEST_ADMIN_USER_ID for gm_id in gm_ids)

    def test_player_role_returns_games_as_player(
        self, db_session, admin_user, regular_user, default_system, default_vtt
    ):
        game = _create_game(
            db_session,
            admin_user,
            default_system,
            default_vtt,
            name="Player User Game",
            status=GAME_STATUS_OPEN,
        )
        game.players.append(regular_user)
        db_session.flush()

        source = MultiDict({"open": "on"})
        user_payload = {"user_id": TEST_REGULAR_USER_ID, "is_admin": False}
        games, _ = get_filtered_user_games(
            source, TEST_REGULAR_USER_ID, user_payload, role="player"
        )
        assert hasattr(games, "items")
        assert any(g.name == "Player User Game" for g in games.items)

    def test_invalid_role_raises_validation_error(self, db_session, admin_user):
        source = MultiDict({})
        user_payload = {"user_id": TEST_ADMIN_USER_ID, "is_admin": True}
        with pytest.raises(ValidationError) as exc_info:
            get_filtered_user_games(
                source, TEST_ADMIN_USER_ID, user_payload, role="invalid"
            )
        assert exc_info.value.field == "role"

    def test_nonexistent_user_returns_empty(self, db_session):
        source = MultiDict({})
        user_payload = {"user_id": "nonexistent", "is_admin": False}
        result, args = get_filtered_user_games(
            source, "nonexistent_user_999", user_payload, role="gm"
        )
        assert result == []
        assert args == {}
