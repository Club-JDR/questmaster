from datetime import datetime
from decimal import Decimal

import pytest

from website.exceptions import ValidationError
from website.models.game import CLASSIFICATION_SCHEMA, Game


@pytest.fixture
def sample_game():
    """Instance de jeu simple pour tests."""
    return Game(
        id=1,
        slug="game-slug",
        name="Test Game",
        type="oneshot",
        length="3h",
        gm_id="gm123",
        system_id=1,
        vtt_id=None,
        description="A test game",
        restriction="all",
        restriction_tags="tag1,tag2",
        party_size=4,
        party_selection=False,
        xp="all",
        date=datetime(2024, 1, 1, 18, 0),
        session_length=Decimal("3.5"),
        frequency="weekly",
        characters="with_gm",
        classification={"action": 1, "investigation": 1, "interaction": 1, "horror": 1},
        ambience=["chill", "comic"],
        complement="Some complement",
        img="img.png",
        channel="channel1",
        msg_id="msg123",
        role="role1",
        status="draft",
        special_event_id=None,
    )


def test_to_dict_basic_fields(sample_game):
    data = sample_game.to_dict()
    assert data["id"] == 1
    assert data["slug"] == "game-slug"
    assert data["type"] == "oneshot"
    assert data["party_size"] == 4
    assert isinstance(data["date"], str)  # isoformat string
    assert data["session_length"] == pytest.approx(3.5)
    assert data["classification"] == {
        "action": 1,
        "investigation": 1,
        "interaction": 1,
        "horror": 1,
    }
    assert data["ambience"] == ["chill", "comic"]
    assert "player_ids" in data


def test_to_json_alias(sample_game):
    assert sample_game.to_json() == sample_game.to_dict()


def test_json_property(sample_game):
    assert sample_game.json == sample_game.to_dict()


def test_from_dict_creates_game():
    data = {
        "id": 2,
        "slug": "another-game",
        "name": "Another Game",
        "type": "campaign",
        "length": "5h",
        "gm_id": "gm456",
        "system_id": 2,
        "vtt_id": 1,
        "description": "Description here",
        "restriction": "16+",
        "restriction_tags": "tag3",
        "party_size": 5,
        "party_selection": True,
        "xp": "beginners",
        "date": "2024-02-01T12:00:00",
        "session_length": 4.0,
        "frequency": "monthly",
        "characters": "self",
        "classification": {
            "action": 0,
            "investigation": 2,
            "interaction": 1,
            "horror": 0,
        },
        "ambience": ["serious"],
        "complement": "Extra info",
        "img": "img2.png",
        "channel": "channel2",
        "msg_id": "msg456",
        "role": "role2",
        "status": "open",
        "special_event_id": 10,
    }
    game = Game.from_dict(data)
    assert isinstance(game, Game)
    assert game.id == 2
    assert game.slug == "another-game"
    assert game.type == "campaign"
    assert game.date == datetime.fromisoformat("2024-02-01T12:00:00")
    assert game.session_length == Decimal("4.0")
    assert game.classification == {
        "action": 0,
        "investigation": 2,
        "interaction": 1,
        "horror": 0,
    }
    assert game.ambience == ["serious"]


def test_from_json_alias():
    data = {
        "id": 3,
        "slug": "json-game",
        "name": "Json Game",
        "type": "oneshot",
        "length": "2h",
        "gm_id": "gm789",
        "system_id": 3,
        "description": "Desc",
        "restriction": "18+",
        "party_size": 3,
        "xp": "seasoned",
        "date": "2024-03-01T10:00:00",
        "session_length": 2.0,
        "status": "closed",
    }
    g1 = Game.from_dict(data)
    g2 = Game.from_json(data)
    assert g1 == g2


def test_update_from_dict_updates_fields(sample_game):
    update = {
        "name": "Updated Game",
        "party_size": 6,
        "date": "2024-04-01T15:00:00",
        "session_length": 5.0,
        "status": "open",
        "slug": "should-not-update",  # protected field, should be ignored
    }
    sample_game.update_from_dict(update)
    assert sample_game.name == "Updated Game"
    assert sample_game.party_size == 6
    assert sample_game.date == datetime.fromisoformat("2024-04-01T15:00:00")
    assert sample_game.session_length == Decimal("5.0")
    assert sample_game.status == "open"
    assert sample_game.slug == "game-slug"  # unchanged


def test_update_from_dict_ignores_relationships_and_protected(sample_game):
    update = {
        "gm": "some gm",
        "players": ["player1", "player2"],
        "sessions": ["session1"],
        "system": 10,
        "vtt": 20,
        "special_event": 30,
        "id": 99,  # protected
    }
    sample_game.update_from_dict(update)
    # None of these should be set via update_from_dict
    assert sample_game.id == 1
    assert getattr(sample_game, "gm") != "some gm"
    assert getattr(sample_game, "players") != ["player1", "player2"]


def test_validate_classification_valid_and_invalid(sample_game):
    # Valid classification should pass
    valid = {"action": 2, "investigation": 0, "interaction": 1, "horror": 2}
    assert sample_game.validate_classification("classification", valid) == valid

    # Invalid classification: value out of range
    invalid = {"action": 3, "investigation": 0, "interaction": 1, "horror": 2}
    with pytest.raises(ValidationError):
        sample_game.validate_classification("classification", invalid)


def test_validate_party_size_valid_and_invalid(sample_game):
    # Valid party size
    assert sample_game.validate_party_size("party_size", 4) == 4
    # Invalid party size (<1)
    with pytest.raises(ValidationError):
        sample_game.validate_party_size("party_size", 0)


def test_repr_contains_info(sample_game):
    rep = repr(sample_game)
    assert "Game" in rep
    assert "game-slug" in rep
    assert "Test Game" in rep
    assert "oneshot" in rep
    assert "draft" in rep


def test_equality_and_inequality():
    g1 = Game(id=1, slug="slug1", name="Game1", type="oneshot", status="draft")
    g2 = Game(id=1, slug="slug1", name="Game1", type="oneshot", status="draft")
    g3 = Game(id=2, slug="slug2", name="Game2", type="campaign", status="open")

    assert g1 == g2
    assert g1 != g3


def test_equality_with_non_game_returns_notimplemented(sample_game):
    assert sample_game.__eq__("not a game") is NotImplemented
