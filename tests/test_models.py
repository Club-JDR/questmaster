import json, os
from website.models import Game, User, System, remove_archived

users = json.loads(os.environ.get("USER_ID_LIST"))


def test_systems():
    name = "D&D 5E"
    icon = "https://club-jdr.fr/wp-content/uploads/2021/12/dnd.png"
    system = System(name=name, icon=icon)
    assert system.name == name
    assert system.icon == icon
    print(system.id)


def test_games():
    game_name = "Baldur's Gate: Descent into Avernus"
    game_type = "campaign"
    game_length = "20+ sessions"
    game_description = """
    Welcome to Baldur's Gate, a city of ambition and corruption.
    You’ve just started your adventuring career, but already find yourself embroiled in a plot that sprawls from the shadows of Baldur's Gate to the front lines of the planes-spanning Blood War!
    Do you have what it takes to turn infernal war machines and nefarious contracts against the archdevil Zariel and her diabolical hordes?
    And can you ever hope to find your way home safely when pitted against the infinite evils of the Nine Hells?

    This heroic Dungeons & Dragons adventure book takes players from levels 1 to 13 as they journey through Baldur's Gate and into Avernus, the first layer of the Nine Hells.
    """
    game_restriction_tags = "psychological violence, gore"
    game = Game(
        name=game_name,
        type=game_type,
        length=game_length,
        system=System(name="5E"),
        description=game_description,
        restriction="16+",
        restriction_tags=game_restriction_tags,
        party_size=4,
        party_selection=False,
        pregen=False,
        status="open",
    )
    assert len(remove_archived([game])) == 1
    game.status = "archived"
    assert len(remove_archived([game])) == 0


def test_users():
    gm = User(users["gm1"])
    assert gm.id == users["gm1"]
