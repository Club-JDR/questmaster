"""Tests for GameRepository."""

import pytest

from tests.constants import TEST_SPECIAL_EVENT_ID
from tests.factories import GameFactory
from website.models import Game
from website.repositories.game import GameRepository


class TestGameRepository:
    def test_get_by_id(self, db_session, sample_game):
        repo = GameRepository()
        game = repo.get_by_id(sample_game.id)
        assert game is not None
        assert game.id == sample_game.id
        assert game.slug == sample_game.slug

    def test_get_by_id_not_found(self, db_session):
        repo = GameRepository()
        game = repo.get_by_id(999999)
        assert game is None

    def test_get_by_slug(self, db_session, sample_game):
        repo = GameRepository()
        game = repo.get_by_slug(sample_game.slug)
        assert game is not None
        assert game.slug == sample_game.slug
        assert game.name == sample_game.name

    def test_get_by_slug_not_found(self, db_session):
        repo = GameRepository()
        game = repo.get_by_slug("nonexistent-slug")
        assert game is None

    def test_get_by_slug_or_404(self, db_session, sample_game):
        repo = GameRepository()
        game = repo.get_by_slug_or_404(sample_game.slug)
        assert game is not None
        assert game.slug == sample_game.slug

    def test_get_by_slug_or_404_raises(self, db_session):
        from werkzeug.exceptions import NotFound

        repo = GameRepository()
        with pytest.raises(NotFound):
            repo.get_by_slug_or_404("nonexistent-slug")

    def test_get_all_slugs(self, db_session, sample_game, published_game):
        repo = GameRepository()
        slugs = repo.get_all_slugs()
        assert isinstance(slugs, set)
        assert sample_game.slug in slugs
        assert published_game.slug in slugs

    def test_find_by_gm(self, db_session, sample_game, published_game, admin_user):
        repo = GameRepository()
        games = repo.find_by_gm(admin_user.id)
        assert len(games) >= 2
        assert all(g.gm_id == admin_user.id for g in games)

    def test_find_by_player(self, db_session, sample_game, regular_user):
        sample_game.players.append(regular_user)
        db_session.flush()

        repo = GameRepository()
        games = repo.find_by_player(regular_user.id)
        assert len(games) >= 1
        assert any(g.id == sample_game.id for g in games)

    def test_find_by_special_event(self, db_session, admin_user, default_system):
        event_game = GameFactory(
            db_session,
            gm_id=admin_user.id,
            system_id=default_system.id,
            special_event_id=TEST_SPECIAL_EVENT_ID,
        )

        repo = GameRepository()
        games = repo.find_by_special_event(TEST_SPECIAL_EVENT_ID)
        assert len(games) >= 1
        assert any(g.id == event_game.id for g in games)

    def test_get_for_update(self, db_session, sample_game):
        repo = GameRepository()
        game = repo.get_for_update(sample_game.id)
        assert game is not None
        assert game.id == sample_game.id

    def test_get_with_relations(self, db_session, sample_game):
        repo = GameRepository()
        game = repo.get_with_relations(sample_game.id)
        assert game is not None
        assert game.gm is not None
        assert game.system is not None
        assert isinstance(game.players, list)

    def test_delete_by_id(self, db_session, sample_game):
        repo = GameRepository()
        game_id = sample_game.id
        repo.delete_by_id(game_id)
        db_session.commit()

        assert repo.get_by_id(game_id) is None

    def test_search_basic(self, db_session, sample_game, published_game):
        repo = GameRepository()
        games, total = repo.search(
            filters={"status": ["open"], "game_type": ["oneshot", "campaign"]},
            page=1,
            per_page=20,
        )
        assert total >= 1
        assert len(games) >= 1

    def test_search_by_status(self, db_session, sample_game, published_game):
        repo = GameRepository()
        user_payload = {"user_id": sample_game.gm_id, "is_admin": True}
        games, _ = repo.search(
            filters={"status": ["draft"]},
            page=1,
            per_page=20,
            user_payload=user_payload,
        )
        assert any(g.status == "draft" for g in games)

    def test_search_by_type(self, db_session, published_game):
        repo = GameRepository()
        games, _ = repo.search(
            filters={"game_type": ["campaign"], "status": ["open"]},
            page=1,
            per_page=20,
        )
        assert all(g.type == "campaign" for g in games)

    def test_search_by_name(self, db_session, published_game):
        repo = GameRepository()
        games, _ = repo.search(
            filters={"name": "Published"},
            page=1,
            per_page=20,
        )
        assert any(g.slug == published_game.slug for g in games)

    def test_search_by_system(self, db_session, sample_game, default_system):
        repo = GameRepository()
        games, _ = repo.search(
            filters={"system_id": default_system.id},
            page=1,
            per_page=20,
        )
        assert all(g.system_id == default_system.id for g in games)

    def test_search_by_gm(self, db_session, sample_game, admin_user):
        repo = GameRepository()
        games, _ = repo.search(
            filters={"gm_id": admin_user.id},
            page=1,
            per_page=20,
        )
        assert all(g.gm_id == admin_user.id for g in games)

    def test_search_pagination(self, db_session, admin_user, default_system):
        for i in range(5):
            GameFactory(
                db_session,
                gm_id=admin_user.id,
                system_id=default_system.id,
                name=f"Paginated Game {i}",
                status="open",
            )

        repo = GameRepository()
        games_p1, total = repo.search(
            filters={"status": ["open"]},
            page=1,
            per_page=3,
        )
        assert len(games_p1) <= 3
        assert total >= 5

        games_p2, total = repo.search(
            filters={"status": ["open"]},
            page=2,
            per_page=3,
        )
        assert len(games_p2) >= 1

    def test_add_and_commit(self, db_session, admin_user, default_system):
        repo = GameRepository()
        game = GameFactory(
            db_session,
            gm_id=admin_user.id,
            system_id=default_system.id,
            name="New Repo Game",
        )

        found = repo.get_by_slug(game.slug)
        assert found is not None
        assert found.name == "New Repo Game"

    def test_count(self, db_session, sample_game, published_game):
        repo = GameRepository()
        count = repo.count()
        assert count >= 2
