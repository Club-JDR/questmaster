import pytest
from website.models import Vtt
from website.services.vtt import VttService
from website.exceptions import NotFoundError, ValidationError


class TestVttService:
    def test_get_all(self, db_session):
        service = VttService()
        vtts = service.get_all()
        assert len(vtts) >= 1
        names = [v.name for v in vtts]
        assert names == sorted(names)

    def test_get_by_id(self, db_session):
        service = VttService()
        vtt = Vtt.query.first()
        found = service.get_by_id(vtt.id)
        assert found.id == vtt.id
        assert found.name == vtt.name

    def test_get_by_id_not_found(self, db_session):
        service = VttService()
        with pytest.raises(NotFoundError):
            service.get_by_id(-999)

    def test_create(self, db_session):
        service = VttService()
        vtt = service.create(name="NewTestVtt", icon="new.png")
        assert vtt.id is not None
        assert vtt.name == "NewTestVtt"
        assert vtt.icon == "new.png"
        db_session.delete(vtt)
        db_session.commit()

    def test_create_duplicate_name(self, db_session):
        service = VttService()
        with pytest.raises(ValidationError) as exc_info:
            service.create(name="Foundry")
        assert exc_info.value.field == "name"

    def test_update(self, db_session):
        service = VttService()
        vtt = service.create(name="VttToUpdate", icon="old.png")
        updated = service.update(vtt.id, {"name": "VttUpdated", "icon": "new.png"})
        assert updated.name == "VttUpdated"
        assert updated.icon == "new.png"
        db_session.delete(updated)
        db_session.commit()

    def test_delete(self, db_session):
        service = VttService()
        vtt = service.create(name="VttToDeleteService", icon="del.png")
        vtt_id = vtt.id
        service.delete(vtt_id)
        assert db_session.get(Vtt, vtt_id) is None
