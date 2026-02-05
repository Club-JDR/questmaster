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
        db_session.rollback()

    def test_inherits_delete(self, db_session):
        repo = SystemRepository()
        new_system = System(name="TestRepoDelete", icon="test.png")
        repo.add(new_system)
        count_before = repo.count()
        repo.delete(new_system)
        assert repo.count() == count_before - 1
        db_session.rollback()
