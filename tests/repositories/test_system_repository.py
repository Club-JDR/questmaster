from datetime import datetime

from tests.factories import GameFactory, GameSessionFactory, SystemFactory, UserFactory
from website.models import System
from website.repositories.system import SystemRepository


class TestSystemRepository:
    def test_get_all_ordered(self, db_session):
        repo = SystemRepository()
        systems = repo.get_all_ordered()
        assert len(systems) >= 1
        names = [s.name for s in systems]
        assert names == sorted(names)

    def test_get_by_name(self, db_session):
        repo = SystemRepository()
        system = repo.get_by_name("Appel de Cthulhu v7")
        assert system is not None
        assert system.name == "Appel de Cthulhu v7"

    def test_get_by_name_not_found(self, db_session):
        repo = SystemRepository()
        assert repo.get_by_name("nonexistent") is None

    def test_inherits_get_by_id(self, db_session):
        repo = SystemRepository()
        system = System.query.first()
        found = repo.get_by_id(system.id)
        assert found is not None
        assert found.id == system.id

    def test_inherits_add(self, db_session):
        repo = SystemRepository()
        new_system = System(name="TestRepoAdd", icon="test.png")
        result = repo.add(new_system)
        assert result.id is not None
        assert result.name == "TestRepoAdd"

    def test_inherits_delete(self, db_session):
        repo = SystemRepository()
        system = SystemFactory(db_session, name="TestRepoDelete")
        count_before = repo.count()
        repo.delete(system)
        assert repo.count() == count_before - 1

    def test_get_gm_history_returns_gms_of_non_draft_games(self, db_session):
        repo = SystemRepository()
        system = SystemFactory(db_session)
        gm = UserFactory(db_session, name="AAA GM With History")
        GameFactory(db_session, system_id=system.id, gm_id=gm.id, status="open")

        history = repo.get_gm_history(system.id)

        assert [u.id for u in history] == [gm.id]

    def test_get_gm_history_excludes_drafts(self, db_session):
        repo = SystemRepository()
        system = SystemFactory(db_session)
        gm = UserFactory(db_session)
        GameFactory(db_session, system_id=system.id, gm_id=gm.id, status="draft")

        assert repo.get_gm_history(system.id) == []

    def test_get_gm_history_deduplicates_and_orders_by_name(self, db_session):
        repo = SystemRepository()
        system = SystemFactory(db_session)
        gm = UserFactory(db_session, name="ZZZ Repeat GM")
        other_gm = UserFactory(db_session, name="AAA Other GM")
        GameFactory(db_session, system_id=system.id, gm_id=gm.id, status="open")
        GameFactory(db_session, system_id=system.id, gm_id=gm.id, status="closed")
        GameFactory(db_session, system_id=system.id, gm_id=other_gm.id, status="archived")

        history = repo.get_gm_history(system.id)

        assert [u.id for u in history] == [other_gm.id, gm.id]

    def test_get_gm_history_empty_for_unrelated_system(self, db_session):
        repo = SystemRepository()
        system = SystemFactory(db_session)
        other_system = SystemFactory(db_session)
        gm = UserFactory(db_session)
        GameFactory(db_session, system_id=other_system.id, gm_id=gm.id, status="open")

        assert repo.get_gm_history(system.id) == []

    def test_get_gm_history_excludes_placeholder_user(self, db_session):
        repo = SystemRepository()
        system = SystemFactory(db_session)
        gm = UserFactory(db_session, name="AAA Real GM")
        placeholder = UserFactory(db_session, name="Inconnu")
        GameFactory(db_session, system_id=system.id, gm_id=gm.id, status="open")
        GameFactory(db_session, system_id=system.id, gm_id=placeholder.id, status="open")

        history = repo.get_gm_history(system.id)

        assert [u.id for u in history] == [gm.id]

    def test_get_gm_stats_tallies_by_type_and_sessions(self, db_session):
        repo = SystemRepository()
        system = SystemFactory(db_session)
        gm = UserFactory(db_session)
        os_game = GameFactory(
            db_session, system_id=system.id, gm_id=gm.id, type="oneshot", status="open"
        )
        campaign_game = GameFactory(
            db_session, system_id=system.id, gm_id=gm.id, type="campaign", status="closed"
        )
        GameSessionFactory(
            db_session,
            game_id=os_game.id,
            start=datetime(2025, 9, 1, 20, 0),
            end=datetime(2025, 9, 1, 23, 0),
        )
        GameSessionFactory(
            db_session,
            game_id=campaign_game.id,
            start=datetime(2025, 9, 8, 20, 0),
            end=datetime(2025, 9, 8, 23, 0),
        )
        GameSessionFactory(
            db_session,
            game_id=campaign_game.id,
            start=datetime(2025, 9, 15, 20, 0),
            end=datetime(2025, 9, 15, 23, 0),
        )

        stats = repo.get_gm_stats(gm.id, system.id)

        assert stats == {"oneshots": 1, "campaigns": 1, "sessions": 3}

    def test_get_gm_stats_excludes_drafts_and_other_systems(self, db_session):
        repo = SystemRepository()
        system = SystemFactory(db_session)
        other_system = SystemFactory(db_session)
        gm = UserFactory(db_session)
        GameFactory(db_session, system_id=system.id, gm_id=gm.id, status="draft")
        GameFactory(db_session, system_id=other_system.id, gm_id=gm.id, status="open")

        stats = repo.get_gm_stats(gm.id, system.id)

        assert stats == {"oneshots": 0, "campaigns": 0, "sessions": 0}

    def test_get_gm_stats_no_history_returns_zeros(self, db_session):
        repo = SystemRepository()
        system = SystemFactory(db_session)
        gm = UserFactory(db_session)

        assert repo.get_gm_stats(gm.id, system.id) == {
            "oneshots": 0,
            "campaigns": 0,
            "sessions": 0,
        }

    def test_get_player_stats_tallies_by_type_and_sessions(self, db_session):
        repo = SystemRepository()
        system = SystemFactory(db_session)
        player = UserFactory(db_session)
        gm = UserFactory(db_session)
        game = GameFactory(
            db_session, system_id=system.id, gm_id=gm.id, type="oneshot", status="open"
        )
        game.players.append(player)
        db_session.flush()
        GameSessionFactory(
            db_session,
            game_id=game.id,
            start=datetime(2025, 9, 1, 20, 0),
            end=datetime(2025, 9, 1, 23, 0),
        )

        stats = repo.get_player_stats(player.id, system.id)

        assert stats == {"oneshots": 1, "campaigns": 0, "sessions": 1}

    def test_get_player_stats_excludes_drafts_and_other_systems(self, db_session):
        repo = SystemRepository()
        system = SystemFactory(db_session)
        other_system = SystemFactory(db_session)
        player = UserFactory(db_session)
        gm = UserFactory(db_session)
        draft_game = GameFactory(db_session, system_id=system.id, gm_id=gm.id, status="draft")
        draft_game.players.append(player)
        other_game = GameFactory(db_session, system_id=other_system.id, gm_id=gm.id, status="open")
        other_game.players.append(player)
        db_session.flush()

        stats = repo.get_player_stats(player.id, system.id)

        assert stats == {"oneshots": 0, "campaigns": 0, "sessions": 0}

    def test_get_player_stats_not_registered_returns_zeros(self, db_session):
        repo = SystemRepository()
        system = SystemFactory(db_session)
        player = UserFactory(db_session)

        assert repo.get_player_stats(player.id, system.id) == {
            "oneshots": 0,
            "campaigns": 0,
            "sessions": 0,
        }
