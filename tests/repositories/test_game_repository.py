"""Tests for GameRepository."""

import pytest

from tests.constants import TEST_SPECIAL_EVENT_ID
from tests.factories import GameFactory, SpecialEventFactory
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

    def test_get_by_channel(self, db_session, admin_user, default_system):
        game = GameFactory(
            db_session,
            gm_id=admin_user.id,
            system_id=default_system.id,
            status="open",
            channel="123456700000000001",
        )
        repo = GameRepository()
        found = repo.get_by_channel("123456700000000001")
        assert found is not None
        assert found.id == game.id
        # Integer channel IDs are coerced to strings before querying
        assert repo.get_by_channel(123456700000000001).id == game.id

    def test_get_by_channel_not_found(self, db_session):
        repo = GameRepository()
        assert repo.get_by_channel("999999999999999999") is None

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

    def test_query_by_special_event(self, db_session, admin_user, default_system):
        event_game = GameFactory(
            db_session,
            gm_id=admin_user.id,
            system_id=default_system.id,
            special_event_id=TEST_SPECIAL_EVENT_ID,
        )

        repo = GameRepository()
        query = repo.query_by_special_event(TEST_SPECIAL_EVENT_ID)
        # Returns a query object, not a list
        games = query.all()
        assert len(games) >= 1
        assert any(g.id == event_game.id for g in games)

    def test_query_by_special_event_empty(self, db_session):
        repo = GameRepository()
        query = repo.query_by_special_event(999999)
        assert query.all() == []

    def test_get_player_leaderboard_for_event(
        self, db_session, admin_user, regular_user, default_system
    ):
        event = SpecialEventFactory(db_session)
        game = GameFactory(
            db_session,
            gm_id=admin_user.id,
            system_id=default_system.id,
            special_event_id=event.id,
            status="archived",
            trophies_awarded=True,
        )
        game.players.append(regular_user)
        db_session.flush()

        repo = GameRepository()
        leaderboard = repo.get_player_leaderboard_for_event(event.id)
        assert leaderboard == [(regular_user, 1)]

    def test_get_player_leaderboard_for_event_ignores_other_events(
        self, db_session, admin_user, regular_user, default_system
    ):
        event = SpecialEventFactory(db_session)
        other_event = SpecialEventFactory(db_session)
        other_game = GameFactory(
            db_session,
            gm_id=admin_user.id,
            system_id=default_system.id,
            special_event_id=other_event.id,
            status="archived",
            trophies_awarded=True,
        )
        other_game.players.append(regular_user)
        db_session.flush()

        repo = GameRepository()
        assert repo.get_player_leaderboard_for_event(event.id) == []

    def test_get_player_leaderboard_for_event_excludes_drafts(
        self, db_session, admin_user, regular_user, default_system
    ):
        """Unpublished draft games never contribute to the leaderboard."""
        event = SpecialEventFactory(db_session)
        draft_game = GameFactory(
            db_session,
            gm_id=admin_user.id,
            system_id=default_system.id,
            special_event_id=event.id,
            status="draft",
        )
        draft_game.players.append(regular_user)
        db_session.flush()

        repo = GameRepository()
        assert repo.get_player_leaderboard_for_event(event.id) == []

    def test_get_player_leaderboard_for_event_excludes_games_without_trophies(
        self, db_session, admin_user, regular_user, default_system
    ):
        """An archived game where the GM opted out of awarding trophies doesn't count."""
        event = SpecialEventFactory(db_session)
        game = GameFactory(
            db_session,
            gm_id=admin_user.id,
            system_id=default_system.id,
            special_event_id=event.id,
            status="archived",
            trophies_awarded=False,
        )
        game.players.append(regular_user)
        db_session.flush()

        repo = GameRepository()
        assert repo.get_player_leaderboard_for_event(event.id) == []

    def test_get_gm_leaderboard_for_event(self, db_session, admin_user, default_system):
        event = SpecialEventFactory(db_session)
        GameFactory(
            db_session,
            gm_id=admin_user.id,
            system_id=default_system.id,
            special_event_id=event.id,
            status="archived",
            trophies_awarded=True,
        )

        repo = GameRepository()
        leaderboard = repo.get_gm_leaderboard_for_event(event.id)
        assert leaderboard == [(admin_user, 1)]

    def test_get_gm_leaderboard_for_event_excludes_drafts(
        self, db_session, admin_user, default_system
    ):
        """Unpublished draft games never contribute to the GM leaderboard."""
        event = SpecialEventFactory(db_session)
        GameFactory(
            db_session,
            gm_id=admin_user.id,
            system_id=default_system.id,
            special_event_id=event.id,
            status="draft",
        )

        repo = GameRepository()
        assert repo.get_gm_leaderboard_for_event(event.id) == []

    def test_get_gm_leaderboard_for_event_excludes_games_without_trophies(
        self, db_session, admin_user, default_system
    ):
        """An archived game where the GM opted out of awarding trophies doesn't count."""
        event = SpecialEventFactory(db_session)
        GameFactory(
            db_session,
            gm_id=admin_user.id,
            system_id=default_system.id,
            special_event_id=event.id,
            status="archived",
            trophies_awarded=False,
        )

        repo = GameRepository()
        assert repo.get_gm_leaderboard_for_event(event.id) == []

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
        result = repo.search(
            filters={"status": ["open"], "game_type": ["oneshot", "campaign"]},
            page=1,
            per_page=20,
        )
        assert result.total >= 1
        assert len(result.items) >= 1

    def test_search_by_status(self, db_session, sample_game, published_game):
        repo = GameRepository()
        user_payload = {"user_id": sample_game.gm_id, "is_admin": True}
        result = repo.search(
            filters={"status": ["draft"]},
            page=1,
            per_page=20,
            user_payload=user_payload,
        )
        assert any(g.status == "draft" for g in result.items)

    def test_search_draft_status_anonymous_sees_nothing(
        self, db_session, sample_game, published_game
    ):
        """An unauthenticated request for drafts must return zero rows.

        Regression test: when none of the requested statuses are visible to
        the caller, ``_build_status_conditions`` returns an empty condition
        list. That must still filter the query down to zero rows — not skip
        the status filter altogether, which would leak every game
        (including other GMs' drafts) to an anonymous visitor.
        """
        repo = GameRepository()
        result = repo.search(
            filters={"status": ["draft"]},
            page=1,
            per_page=20,
            user_payload=None,
        )
        assert result.total == 0
        assert result.items == []

    def test_search_by_type(self, db_session, published_game):
        repo = GameRepository()
        result = repo.search(
            filters={"game_type": ["campaign"], "status": ["open"]},
            page=1,
            per_page=20,
        )
        assert all(g.type == "campaign" for g in result.items)

    def test_search_by_name(self, db_session, published_game):
        repo = GameRepository()
        result = repo.search(
            filters={"name": "Published"},
            page=1,
            per_page=20,
        )
        assert any(g.slug == published_game.slug for g in result.items)

    def test_search_by_system(self, db_session, sample_game, default_system):
        repo = GameRepository()
        result = repo.search(
            filters={"system_id": default_system.id},
            page=1,
            per_page=20,
        )
        assert all(g.system_id == default_system.id for g in result.items)

    def test_search_by_gm(self, db_session, sample_game, admin_user):
        repo = GameRepository()
        result = repo.search(
            filters={"gm_id": admin_user.id},
            page=1,
            per_page=20,
        )
        assert all(g.gm_id == admin_user.id for g in result.items)

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
        result_p1 = repo.search(
            filters={"status": ["open"]},
            page=1,
            per_page=3,
        )
        assert len(result_p1.items) <= 3
        assert result_p1.total >= 5

        result_p2 = repo.search(
            filters={"status": ["open"]},
            page=2,
            per_page=3,
        )
        assert len(result_p2.items) >= 1

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

    def test_find_by_viewer(self, db_session, sample_game, admin_user, default_system):
        from tests.factories import UserFactory
        from website.models import GameViewer

        repo = GameRepository()
        viewer = UserFactory(db_session)
        other_game = GameFactory(
            db_session, gm_id=admin_user.id, system_id=default_system.id, status="draft"
        )
        db_session.add(GameViewer(game_id=sample_game.id, user_id=viewer.id))
        db_session.flush()

        games = repo.find_by_viewer(viewer.id)

        assert sample_game in games
        assert other_game not in games

    def test_find_by_viewer_with_relations_excludes_drafts(
        self, db_session, admin_user, default_system
    ):
        from tests.factories import UserFactory
        from website.models import GameViewer

        repo = GameRepository()
        viewer = UserFactory(db_session)
        draft = GameFactory(
            db_session,
            gm_id=admin_user.id,
            system_id=default_system.id,
            status="draft",
            open_to_viewers=True,
        )
        db_session.add(GameViewer(game_id=draft.id, user_id=viewer.id))
        db_session.flush()

        games = repo.find_by_viewer_with_relations(viewer.id)

        assert draft not in games
