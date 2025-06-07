import pytest
from website.models import (
    User, Trophy, UserTrophy, Vtt, System,
    Channel, Game, GameEvent, GameSession
)
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError



def test_user_creation(session):
    user = User(id="12345678901234567")
    session.add(user)
    session.commit()
    assert user.id == "12345678901234567"


def test_invalid_user_id():
    with pytest.raises(ValueError):
        User(id="invalid_id")


def test_trophy_and_user_trophy(session):
    user = User(id="11111111111111111")
    trophy = Trophy(name="Badge OS", icon="icon.png", unique=True)
    session.add_all([user, trophy])
    session.commit()

    user_trophy = UserTrophy(user_id=user.id, trophy_id=trophy.id, quantity=1)
    session.add(user_trophy)
    session.commit()

    assert user_trophy.quantity == 1
    assert user_trophy.user == user
    assert user_trophy.trophy == trophy


def test_vtt_model(session):
    vtt = Vtt(name="Roll20", icon="vtt.png")
    session.add(vtt)
    session.commit()
    assert vtt.name == "Roll20"


def test_system_model(session):
    system = System(name="D&D 5e", icon="dnd.png")
    session.add(system)
    session.commit()
    assert system.name == "D&D 5e"


def test_channel_model(session):
    channel = Channel(id="99999999999999999", type="oneshot", size=5)
    session.add(channel)
    session.commit()
    assert channel.type == "oneshot"


def test_game_model(session):
    user = User(id="22222222222222222")
    system = System(name="Pathfinder", icon=None)
    vtt = Vtt(name="Foundry", icon=None)
    session.add_all([user, system, vtt])
    session.commit()

    game = Game(
        slug="slug123",
        name="Test Game",
        type="oneshot",
        length="3h",
        gm_id=user.id,
        system_id=system.id,
        vtt_id=vtt.id,
        description="An exciting test game.",
        restriction="all",
        party_size=4,
        date=datetime.now(),
        session_length=3.0,
        frequency="weekly",
        characters="with_gm",
        classification={"action": 1, "investigation": 1, "interaction": 1, "horror": 1},
        ambience=["chill"],
        complement="Extra info.",
        status="draft"
    )
    session.add(game)
    session.commit()
    assert game.name == "Test Game"
    assert game.status == "draft"


def test_game_session_model(session):
    game = Game.query.first()
    start = datetime.now()
    end = start + timedelta(hours=3)
    session_obj = GameSession(game_id=game.id, start=start, end=end)
    session.add(session_obj)
    session.commit()
    assert session_obj.game == game


def test_game_event_model(session):
    game = Game.query.first()
    event = GameEvent(game_id=game.id, event_type="Test", description="Testing event")
    session.add(event)
    session.commit()
    assert event.event_type == "Test"
    assert event.game == game


def test_duplicate_unique_trophy(session):
    user = User(id="33333333333333333")
    trophy = Trophy(name="UniqueAward", icon="medal.png", unique=True)
    session.add_all([user, trophy])
    session.commit()

    user_trophy1 = UserTrophy(user_id=user.id, trophy_id=trophy.id, quantity=1)
    session.add(user_trophy1)
    session.commit()

    user_trophy2 = UserTrophy(user_id=user.id, trophy_id=trophy.id, quantity=1)
    session.add(user_trophy2)
    with pytest.raises(IntegrityError):
        session.commit()
