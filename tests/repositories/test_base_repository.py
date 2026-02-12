import pytest
from website.models import System
from website.repositories.base import BaseRepository

from tests.factories import SystemFactory


class ConcreteRepository(BaseRepository[System]):
    model_class = System


class TestBaseRepository:
    def test_get_by_id(self, db_session):
        repo = ConcreteRepository()
        system = System.query.first()
        found = repo.get_by_id(system.id)
        assert found is not None
        assert found.id == system.id

    def test_get_by_id_not_found(self, db_session):
        repo = ConcreteRepository()
        assert repo.get_by_id(-999) is None

    def test_get_by_id_or_404(self, db_session):
        repo = ConcreteRepository()
        system = System.query.first()
        found = repo.get_by_id_or_404(system.id)
        assert found.id == system.id

    def test_get_by_id_or_404_raises(self, db_session):
        repo = ConcreteRepository()
        with pytest.raises(Exception):
            repo.get_by_id_or_404(-999)

    def test_get_all(self, db_session):
        repo = ConcreteRepository()
        results = repo.get_all()
        assert isinstance(results, list)
        assert len(results) >= 1

    def test_add_and_count(self, db_session):
        repo = ConcreteRepository()
        initial_count = repo.count()
        new_system = System(name="TestBaseRepoSystem", icon="test.png")
        result = repo.add(new_system)
        assert result is new_system
        assert result.id is not None
        assert repo.count() == initial_count + 1

    def test_delete(self, db_session):
        repo = ConcreteRepository()
        system = SystemFactory(db_session, name="ToDelete", icon="del.png")
        initial_count = repo.count()
        repo.delete(system)
        assert repo.count() == initial_count - 1

    def test_count(self, db_session):
        repo = ConcreteRepository()
        count = repo.count()
        assert isinstance(count, int)
        assert count >= 1
