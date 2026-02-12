from tests.factories import VttFactory
from website.models import Vtt
from website.repositories.vtt import VttRepository


class TestVttRepository:
    def test_get_all_ordered(self, db_session):
        repo = VttRepository()
        vtts = repo.get_all_ordered()
        assert len(vtts) >= 1
        names = [v.name for v in vtts]
        assert names == sorted(names)

    def test_get_by_name(self, db_session):
        repo = VttRepository()
        vtt = repo.get_by_name("Foundry")
        assert vtt is not None
        assert vtt.name == "Foundry"

    def test_get_by_name_not_found(self, db_session):
        repo = VttRepository()
        assert repo.get_by_name("nonexistent") is None

    def test_inherits_get_by_id(self, db_session):
        repo = VttRepository()
        vtt = Vtt.query.first()
        found = repo.get_by_id(vtt.id)
        assert found is not None
        assert found.id == vtt.id

    def test_inherits_add(self, db_session):
        repo = VttRepository()
        new_vtt = Vtt(name="TestVttRepoAdd", icon="test.png")
        result = repo.add(new_vtt)
        assert result.id is not None
        assert result.name == "TestVttRepoAdd"

    def test_inherits_delete(self, db_session):
        repo = VttRepository()
        vtt = VttFactory(db_session, name="TestVttRepoDelete")
        count_before = repo.count()
        repo.delete(vtt)
        assert repo.count() == count_before - 1
