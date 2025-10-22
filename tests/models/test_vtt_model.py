import pytest
from website.models.vtt import Vtt


@pytest.fixture
def sample_vtt():
    return Vtt(id=1, name="Roll20", icon="/img/roll20.png")


def test_to_dict_and_back(sample_vtt):
    d = sample_vtt.to_dict()
    assert d["id"] == 1
    assert d["name"] == "Roll20"

    v2 = Vtt.from_dict(d)
    assert v2 == sample_vtt


def test_update_from_dict(sample_vtt):
    sample_vtt.update_from_dict({"name": "Foundry", "icon": "/img/fvtt.png"})
    assert sample_vtt.name == "Foundry"
    assert sample_vtt.icon == "/img/fvtt.png"


def test_repr_and_eq(sample_vtt):
    rep = repr(sample_vtt)
    assert "Roll20" in rep

    v2 = Vtt(id=1, name="Roll20", icon="/img/roll20.png")
    assert sample_vtt == v2
    assert sample_vtt != Vtt(id=2, name="Other", icon=None)


def test_update_ignores_protected_and_relationship(sample_vtt):
    sample_vtt.update_from_dict({"id": 99, "games_vtt": []})
    assert sample_vtt.id == 1
