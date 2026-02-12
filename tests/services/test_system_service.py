import pytest

from website.exceptions import NotFoundError, ValidationError
from website.models import System
from website.services.system import SystemService


class TestSystemService:
    def test_get_all(self, db_session):
        service = SystemService()
        systems = service.get_all()
        assert len(systems) >= 1
        names = [s.name for s in systems]
        assert names == sorted(names)

    def test_get_by_id(self, db_session):
        service = SystemService()
        system = System.query.first()
        found = service.get_by_id(system.id)
        assert found.id == system.id
        assert found.name == system.name

    def test_get_by_id_not_found(self, db_session):
        service = SystemService()
        with pytest.raises(NotFoundError):
            service.get_by_id(-999)

    def test_create(self, db_session):
        service = SystemService()
        system = service.create(name="NewTestSystem", icon="new.png")
        assert system.id is not None
        assert system.name == "NewTestSystem"
        assert system.icon == "new.png"

    def test_create_duplicate_name(self, db_session):
        service = SystemService()
        with pytest.raises(ValidationError) as exc_info:
            service.create(name="Appel de Cthulhu v7")
        assert exc_info.value.field == "name"

    def test_update(self, db_session):
        service = SystemService()
        system = service.create(name="ToUpdate", icon="old.png")
        updated = service.update(system.id, {"name": "Updated", "icon": "new.png"})
        assert updated.name == "Updated"
        assert updated.icon == "new.png"

    def test_delete(self, db_session):
        service = SystemService()
        system = service.create(name="ToDeleteService", icon="del.png")
        system_id = system.id
        service.delete(system_id)
        assert db_session.get(System, system_id) is None
