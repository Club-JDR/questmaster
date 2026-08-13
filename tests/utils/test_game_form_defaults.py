"""Unit tests for website.utils.game_form_defaults module."""

from types import SimpleNamespace

from website.utils.game_form_defaults import (
    ALL_FIELDS,
    APP_DEFAULTS,
    resolve_game_form_defaults,
    sanitize_user_defaults,
)


def _fake_game(**overrides):
    """Build a lightweight stand-in for a Game ORM instance."""
    base = dict(
        type="campaign",
        system_id=7,
        vtt_id=3,
        session_length=4.0,
        party_size=6,
        party_selection=True,
        xp="seasoned",
        characters="pregen",
        ambience=["epic", "serious"],
        description="Existing description",
        complement="Existing complement",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


class TestSanitizeUserDefaults:
    def test_keeps_only_whitelisted_fields(self):
        data = {"description": "Hi", "classification": {"action": 2}, "restriction": "18+"}
        assert sanitize_user_defaults(data) == {"description": "Hi"}

    def test_blank_text_is_dropped(self):
        assert sanitize_user_defaults({"description": "   "}) == {}

    def test_type_must_be_a_real_game_type(self):
        assert sanitize_user_defaults({"type": "oneshot"}) == {"type": "oneshot"}
        assert sanitize_user_defaults({"type": "specialevent-5"}) == {}

    def test_session_length_bounds(self):
        assert sanitize_user_defaults({"session_length": "4"}) == {"session_length": 4.0}
        assert sanitize_user_defaults({"session_length": "0.1"}) == {}
        assert sanitize_user_defaults({"session_length": "25"}) == {}
        assert sanitize_user_defaults({"session_length": "not-a-number"}) == {}

    def test_party_size_bounds(self):
        assert sanitize_user_defaults({"party_size": "10"}) == {"party_size": 10}
        assert sanitize_user_defaults({"party_size": "0"}) == {}
        assert sanitize_user_defaults({"party_size": "100"}) == {}

    def test_party_selection_accepts_checkbox_value(self):
        assert sanitize_user_defaults({"party_selection": "on"}) == {"party_selection": True}

    def test_party_selection_absent_when_unchecked(self):
        # Unchecked HTML checkboxes are simply absent from form data.
        assert sanitize_user_defaults({}) == {}

    def test_ambience_filters_invalid_keys(self):
        assert sanitize_user_defaults({"ambience": ["chill", "bogus"]}) == {"ambience": ["chill"]}
        assert sanitize_user_defaults({"ambience": []}) == {}
        assert sanitize_user_defaults({"ambience": "chill"}) == {}

    def test_xp_and_characters_enums(self):
        assert sanitize_user_defaults({"xp": "beginners"}) == {"xp": "beginners"}
        assert sanitize_user_defaults({"xp": "nope"}) == {}
        assert sanitize_user_defaults({"characters": "self"}) == {"characters": "self"}
        assert sanitize_user_defaults({"characters": "nope"}) == {}

    def test_system_and_vtt_must_be_positive_ints(self):
        assert sanitize_user_defaults({"system": "5"}) == {"system": 5}
        assert sanitize_user_defaults({"system": "-1"}) == {}
        assert sanitize_user_defaults({"system": "abc"}) == {}
        assert sanitize_user_defaults({"vtt": "3"}) == {"vtt": 3}


class TestResolveGameFormDefaultsNoGame:
    def test_no_user_uses_pure_app_defaults(self):
        resolved = resolve_game_form_defaults()
        assert resolved == {field: APP_DEFAULTS.get(field) for field in ALL_FIELDS}

    def test_user_default_overrides_app_default(self):
        user = SimpleNamespace(game_defaults={"description": "My canvas", "xp": "beginners"})
        resolved = resolve_game_form_defaults(user=user)
        assert resolved["description"] == "My canvas"
        assert resolved["xp"] == "beginners"
        # Untouched fields still fall back to app defaults.
        assert resolved["characters"] == APP_DEFAULTS["characters"]

    def test_user_default_for_unwhitelisted_key_has_no_effect(self):
        user = SimpleNamespace(game_defaults={"restriction": "18+", "img": "https://x"})
        resolved = resolve_game_form_defaults(user=user)
        assert "restriction" not in resolved
        assert "img" not in resolved

    def test_stale_system_reference_is_dropped(self):
        user = SimpleNamespace(game_defaults={"system": 999})
        systems = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
        resolved = resolve_game_form_defaults(user=user, systems=systems)
        assert resolved["system"] is None

    def test_valid_system_reference_is_kept(self):
        user = SimpleNamespace(game_defaults={"system": 2})
        systems = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
        resolved = resolve_game_form_defaults(user=user, systems=systems)
        assert resolved["system"] == 2

    def test_no_systems_list_skips_stale_check(self):
        user = SimpleNamespace(game_defaults={"system": 999})
        resolved = resolve_game_form_defaults(user=user)
        assert resolved["system"] == 999

    def test_no_game_defaults_on_user_uses_app_defaults(self):
        user = SimpleNamespace(game_defaults=None)
        resolved = resolve_game_form_defaults(user=user)
        assert resolved == {field: APP_DEFAULTS.get(field) for field in ALL_FIELDS}


class TestResolveGameFormDefaultsWithGame:
    def test_game_value_wins_over_user_default(self):
        game = _fake_game(description="Game description")
        user = SimpleNamespace(game_defaults={"description": "User canvas"})
        resolved = resolve_game_form_defaults(game=game, user=user)
        assert resolved["description"] == "Game description"

    def test_all_fields_reflect_game(self):
        game = _fake_game()
        resolved = resolve_game_form_defaults(game=game)
        assert resolved["type"] == "campaign"
        assert resolved["system"] == 7
        assert resolved["vtt"] == 3
        assert resolved["session_length"] == 4.0
        assert resolved["party_size"] == 6
        assert resolved["party_selection"] is True
        assert resolved["xp"] == "seasoned"
        assert resolved["characters"] == "pregen"
        assert resolved["ambience"] == ["epic", "serious"]
        assert resolved["description"] == "Existing description"
        assert resolved["complement"] == "Existing complement"

    def test_none_ambience_becomes_empty_list(self):
        game = _fake_game(ambience=None)
        resolved = resolve_game_form_defaults(game=game)
        assert resolved["ambience"] == []

    def test_none_complement_becomes_empty_string(self):
        game = _fake_game(complement=None)
        resolved = resolve_game_form_defaults(game=game)
        assert resolved["complement"] == ""
