import json, os
from datetime import datetime
from website.models import Game, User, System, Vtt, GameSession, Channel

users = json.loads(os.environ.get("USER_ID_LIST"))


def test_systems():
    name = "D&D 5E"
    icon = "https://club-jdr.fr/wp-content/uploads/2021/12/dnd.png"
    system = System(name=name, icon=icon)
    assert system.name == name
    assert system.icon == icon


def test_channels():
    id = "1234567890"
    type = "oneshot"
    size = 15
    channel = Channel(id=id, type=type, size=size)
    assert channel.id == id
    assert channel.type == type
    assert channel.size == size


def test_vtts():
    name = "Foundry"
    icon = "https://foundryvtt.wiki/fvtt-solid-512.png"
    vtt = Vtt(name=name, icon=icon)
    assert vtt.name == name
    assert vtt.icon == icon


def test_games():
    game_name = "Baldur's Gate: Descent into Avernus"
    game_type = "campaign"
    game_length = "20+ sessions"
    game_session_length = 3.5
    game_description = """
    Welcome to Baldur's Gate, a city of ambition and corruption.
    You’ve just started your adventuring career, but already find yourself embroiled in a plot that sprawls from the shadows of Baldur's Gate to the front lines of the planes-spanning Blood War!
    Do you have what it takes to turn infernal war machines and nefarious contracts against the archdevil Zariel and her diabolical hordes?
    And can you ever hope to find your way home safely when pitted against the infinite evils of the Nine Hells?

    This heroic Dungeons & Dragons adventure book takes players from levels 1 to 13 as they journey through Baldur's Gate and into Avernus, the first layer of the Nine Hells.
    """
    game_restriction_tags = "psychological violence, gore"
    game_classification = {
        "action": 2,
        "investigation": 0,
        "interaction": 1,
        "horror": 0,
    }
    game_ambience = ["epic", "serious"]
    now = datetime.now()
    game_date = now.strftime("%Y-%m-%d %H:%M")
    game_system = System(name="5E")
    game_vtt = Vtt(name="Foundry")
    game_restriction = "16+"
    game_size = 4
    game_status = "open"
    game_frequency = "weekly"
    game = Game(
        name=game_name,
        type=game_type,
        length=game_length,
        system=game_system,
        vtt=game_vtt,
        description=game_description,
        restriction=game_restriction,
        restriction_tags=game_restriction_tags,
        party_size=game_size,
        status=game_status,
        ambience=game_ambience,
        classification=game_classification,
        date=game_date,
        session_length=game_session_length,
        frequency=game_frequency,
    )
    assert game.name == game_name
    assert game.type == game_type
    assert game.length == game_length
    assert game.description == game_description
    assert game.ambience == game_ambience
    assert game.classification == game_classification
    assert game.status == game_status
    assert game.date == game_date
    assert game.system == game_system
    assert game.vtt == game_vtt
    assert game.session_length == game_session_length
    assert game.frequency == game_frequency


def test_users():
    gm = User(users["gm1"])
    assert gm.id == users["gm1"]


def test_sessions():
    start = datetime.strptime("2023-11-01 20:00", "%Y-%m-%d %H:%M")
    end = datetime.strptime("2023-11-01 23:30", "%Y-%m-%d %H:%M")
    session = GameSession(start=start, end=end)
    assert session.start == start
    assert session.end == end
