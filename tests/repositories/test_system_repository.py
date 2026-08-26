from tests.factories import GameFactory, SystemFactory, UserFactory
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
