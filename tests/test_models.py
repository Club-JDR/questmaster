import pytest
from website.models import (
    User,
    Trophy,
    UserTrophy,
    Vtt,
    System,
    Channel,
    Game,
    GameSession,
    GameEvent,
    SpecialEvent,
)
from datetime import datetime, timedelta
import sqlalchemy.exc


def test_user_creation(db_session):
    user = User(id="12345678901234567")
    db_session.add(user)
    db_session.commit()
    assert user.id == "12345678901234567"


def test_invalid_user_id():
    with pytest.raises(ValueError):
        User(id="invalid_id")


def test_user_retrieval(regular_user):
    print(regular_user)
    assert regular_user.id == "698965618279317624"
    assert not getattr(regular_user, "is_admin", False)


def test_vtt_model(db_session):
    vtt = Vtt(name="Roll20", icon="vtt.png")
    db_session.add(vtt)
    db_session.commit()
    assert vtt.name == "Roll20"


def test_system_model(db_session):
    system = System(name="D&D 5e", icon="dnd.png")
    db_session.add(system)
    db_session.commit()
    assert system.name == "D&D 5e"


def test_channel_model(db_session):
    channel = Channel(id="99999999999999999", type="oneshot", size=5)
    db_session.add(channel)
    db_session.commit()
    assert channel.type == "oneshot"


def test_game_model(db_session, default_system, default_vtt):
    user = User(id="22222222222222222")
    db_session.add_all([user, default_system, default_vtt])
    db_session.commit()

    game = Game(
        slug="slug123",
        name="Test Game",
        type="oneshot",
        length="3h",
        gm_id=user.id,
        system_id=default_system.id,
        vtt_id=default_vtt.id,
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
        status="draft",
    )
    db_session.add(game)
    db_session.commit()
    assert game.name == "Test Game"
    assert game.status == "draft"


def test_game_session_model(db_session):
    game = Game.query.first()
    start = datetime.now()
    end = start + timedelta(hours=3)
    session_obj = GameSession(game_id=game.id, start=start, end=end)
    db_session.add(session_obj)
    db_session.commit()
    assert session_obj.game == game


def test_game_event_model(db_session):
    game = Game.query.first()
    event = GameEvent(
        action="create",
        game_id=game.id,
        description="Game created by GM.",
    )
    db_session.add(event)
    db_session.commit()

    assert event.id is not None
    assert event.timestamp is not None
    assert event.action == "create"
    assert event.game_id == game.id
    assert event.description == "Game created by GM."
    assert event.game == game


def test_trophy_and_user_trophy(db_session, regular_user):
    trophy = Trophy(id=100, name="Badge test", icon="icon.png", unique=True)
    db_session.add_all([regular_user, trophy])
    db_session.commit()
    user_trophy = UserTrophy(user_id=regular_user.id, trophy_id=trophy.id, quantity=1)
    db_session.add(user_trophy)
    db_session.commit()
    assert user_trophy.quantity == 1
    assert user_trophy.user == regular_user
    assert user_trophy.trophy == trophy


def test_duplicate_unique_trophy(db_session, regular_user):
    trophy = Trophy(id=200, name="UniqueAward", icon="medal.png", unique=True)
    db_session.add_all([regular_user, trophy])
    db_session.commit()
    user_trophy1 = UserTrophy(user_id=regular_user.id, trophy_id=trophy.id, quantity=1)
    db_session.add(user_trophy1)
    db_session.commit()
    db_session.expunge(user_trophy1)
    user_trophy2 = UserTrophy(user_id=regular_user.id, trophy_id=trophy.id, quantity=1)
    db_session.add(user_trophy2)
    with pytest.raises(sqlalchemy.exc.IntegrityError) as exc_info:
        db_session.commit()
    assert "duplicate key" in str(exc_info.value) or "UNIQUE constraint" in str(
        exc_info.value
    )


def test_special_event(db_session):
    event = SpecialEvent(name="Halloween 2025", color=0xFF6600, active=True)
    db_session.add(event)
    db_session.commit()
    return event
