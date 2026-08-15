import pytest

from website.models.system import System


@pytest.fixture
def sample_system():
    """Reusable System instance."""
    return System(
        id=1,
        name="Call of Cthulhu",
        icon="/img/cthulhu.png",
        description="Une enquête lovecraftienne.",
        reference_url="https://legrog.org/jeux/call-of-cthulhu",
    )


def test_to_dict(sample_system):
    data = sample_system.to_dict()
    assert data == {
        "id": 1,
        "name": "Call of Cthulhu",
        "icon": "/img/cthulhu.png",
        "description": "Une enquête lovecraftienne.",
        "reference_url": "https://legrog.org/jeux/call-of-cthulhu",
    }


def test_to_dict_without_optional_fields():
    system = System(id=2, name="Rêve de Dragon", icon=None)
    data = system.to_dict()
    assert data["description"] is None
    assert data["reference_url"] is None


def test_from_dict_creates_system():
    data = {
        "id": 2,
        "name": "Dungeons & Dragons",
        "icon": "/img/dnd.png",
        "description": "Le classique.",
        "reference_url": "https://legrog.org/jeux/dnd",
    }
    system = System.from_dict(data)
    assert isinstance(system, System)
    assert system.id == 2
    assert system.name == "Dungeons & Dragons"
    assert system.icon == "/img/dnd.png"
    assert system.description == "Le classique."
    assert system.reference_url == "https://legrog.org/jeux/dnd"


def test_update_from_dict(sample_system):
    update = {
        "name": "Delta Green",
        "icon": "/img/delta-green.png",
        "description": "Horreur moderne.",
        "reference_url": "https://legrog.org/jeux/delta-green",
    }
    updated = sample_system.update_from_dict(update)
    assert updated is sample_system
    assert sample_system.name == "Delta Green"
    assert sample_system.icon == "/img/delta-green.png"
    assert sample_system.description == "Horreur moderne."
    assert sample_system.reference_url == "https://legrog.org/jeux/delta-green"


def test_update_from_dict_ignores_unknown_fields(sample_system):
    sample_system.update_from_dict({"unknown": "value"})
    assert not hasattr(sample_system, "unknown")


def test_repr_contains_info(sample_system):
    rep = repr(sample_system)
    assert "System" in rep
    assert "Call of Cthulhu" in rep
    assert "/img/cthulhu.png" in rep


def test_equality_and_inequality():
    s1 = System(id=1, name="D&D 5e", icon="/img/dnd.png")
    s2 = System(id=1, name="D&D 5e", icon="/img/dnd.png")
    s3 = System(id=2, name="Pathfinder", icon="/img/pf.png")

    assert s1 == s2
    assert s1 != s3


def test_equality_considers_description_and_reference_url():
    s1 = System(id=1, name="D&D 5e", icon="/img/dnd.png", description="Un jeu.")
    s2 = System(id=1, name="D&D 5e", icon="/img/dnd.png", description="Un autre texte.")

    assert s1 != s2


def test_equality_with_non_system_returns_notimplemented(sample_system):
    assert sample_system.__eq__("not a system") is NotImplemented


def test_update_from_dict_ignores_protected_fields(sample_system):
    sample_system.update_from_dict(
        {
            "id": 999,
            "games_system": ["should_be_ignored"],
            "name": "Pathfinder 2e",
        }
    )
    # Protected field "id" unchanged
    assert sample_system.id == 1
    # Regular field updated normally
    assert sample_system.name == "Pathfinder 2e"
