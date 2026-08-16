from tests.factories import UserFactory
from website.models import GameViewer
from website.repositories.game_viewer import GameViewerRepository


class TestGameViewerRepository:
    def test_get_returns_none_when_absent(self, db_session, sample_game):
        repo = GameViewerRepository()
        user = UserFactory(db_session)
        assert repo.get(sample_game.id, user.id) is None

    def test_get_returns_existing_follow(self, db_session, sample_game):
        repo = GameViewerRepository()
        user = UserFactory(db_session)
        repo.add(GameViewer(game_id=sample_game.id, user_id=user.id))

        found = repo.get(sample_game.id, user.id)

        assert found is not None
        assert found.game_id == sample_game.id
        assert found.user_id == user.id

    def test_inherits_delete(self, db_session, sample_game):
        repo = GameViewerRepository()
        user = UserFactory(db_session)
        viewer = repo.add(GameViewer(game_id=sample_game.id, user_id=user.id))

        repo.delete(viewer)

        assert repo.get(sample_game.id, user.id) is None
