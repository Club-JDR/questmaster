import pytest

from website.models.game_viewer import GameViewer


@pytest.fixture
def sample_viewer():
    """Reusable GameViewer instance."""
    return GameViewer(game_id=1, user_id="111111111111111111")


def test_to_dict(sample_viewer):
    data = sample_viewer.to_dict()
    assert data["game_id"] == 1
    assert data["user_id"] == "111111111111111111"


def test_from_dict_creates_viewer():
    data = {"game_id": 2, "user_id": "222222222222222222"}
    viewer = GameViewer.from_dict(data)
    assert isinstance(viewer, GameViewer)
    assert viewer.game_id == 2
    assert viewer.user_id == "222222222222222222"


def test_repr_contains_info(sample_viewer):
    rep = repr(sample_viewer)
    assert "GameViewer" in rep
    assert "1" in rep
    assert "111111111111111111" in rep


def test_equality_and_inequality():
    v1 = GameViewer(game_id=1, user_id="1")
    v2 = GameViewer(game_id=1, user_id="1")
    v3 = GameViewer(game_id=1, user_id="2")

    assert v1 == v2
    assert v1 != v3


def test_equality_with_non_viewer_returns_notimplemented(sample_viewer):
    assert sample_viewer.__eq__("not a viewer") is NotImplemented
