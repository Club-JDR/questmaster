import pytest

from tests.factories import GameFactory, SystemFactory, UserFactory
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
        system = service.create(
            name="NewTestSystem",
            icon="new.png",
            description="Un jeu de test.",
            reference_url="https://legrog.org/jeux/new-test-system",
        )
        assert system.id is not None
        assert system.name == "NewTestSystem"
        assert system.icon == "new.png"
        assert system.description == "Un jeu de test."
        assert system.reference_url == "https://legrog.org/jeux/new-test-system"

    def test_create_duplicate_name(self, db_session):
        service = SystemService()
        with pytest.raises(ValidationError) as exc_info:
            service.create(name="Appel de Cthulhu v7")
        assert exc_info.value.field == "name"

    def test_create_rejects_malformed_reference_url(self, db_session):
        service = SystemService()
        with pytest.raises(ValidationError) as exc_info:
            service.create(name="BadUrlSystem", reference_url="not-a-url")
        assert exc_info.value.field == "reference_url"

    def test_update(self, db_session):
        service = SystemService()
        system = service.create(name="ToUpdate", icon="old.png")
        updated = service.update(
            system.id,
            {"name": "Updated", "icon": "new.png", "description": "Nouvelle description."},
        )
        assert updated.name == "Updated"
        assert updated.icon == "new.png"
        assert updated.description == "Nouvelle description."

    def test_update_rejects_malformed_reference_url(self, db_session):
        service = SystemService()
        system = service.create(name="ToUpdateBadUrl")
        with pytest.raises(ValidationError) as exc_info:
            service.update(system.id, {"reference_url": "ftp://not-http"})
        assert exc_info.value.field == "reference_url"

    def test_update_allows_clearing_reference_url(self, db_session):
        service = SystemService()
        system = service.create(name="ToClearUrl", reference_url="https://example.com")
        updated = service.update(system.id, {"reference_url": None})
        assert updated.reference_url is None

    def test_delete(self, db_session):
        service = SystemService()
        system = service.create(name="ToDeleteService", icon="del.png")
        system_id = system.id
        service.delete(system_id)
        assert db_session.get(System, system_id) is None


class TestSystemRunHistory:
    def test_get_run_history_returns_gms(self, db_session):
        service = SystemService()
        system = SystemFactory(db_session)
        gm = UserFactory(db_session)
        GameFactory(db_session, system_id=system.id, gm_id=gm.id, status="open")

        history = service.get_run_history(system.id)

        assert [u.id for u in history] == [gm.id]

    def test_get_run_history_not_found(self, db_session):
        service = SystemService()
        with pytest.raises(NotFoundError):
            service.get_run_history(-999)


class TestSystemInterests:
    def test_get_interested_empty_by_default(self, db_session):
        service = SystemService()
        system = SystemFactory(db_session)
        assert service.get_interested(system.id, "player") == []

    def test_get_interested_invalid_role(self, db_session):
        service = SystemService()
        system = SystemFactory(db_session)
        with pytest.raises(ValidationError) as exc_info:
            service.get_interested(system.id, "spectator")
        assert exc_info.value.field == "role"

    def test_get_user_interests_defaults_false(self, db_session):
        service = SystemService()
        system = SystemFactory(db_session)
        user = UserFactory(db_session)
        assert service.get_user_interests(system.id, user.id) == {"player": False, "gm": False}

    def test_toggle_interest_adds_then_removes(self, db_session):
        service = SystemService()
        system = SystemFactory(db_session)
        user = UserFactory(db_session)

        added = service.toggle_interest(system.id, user.id, "player", note="Dispo le soir")
        assert added is True
        assert service.get_user_interests(system.id, user.id)["player"] is True
        assert [i.user_id for i in service.get_interested(system.id, "player")] == [user.id]

        removed = service.toggle_interest(system.id, user.id, "player")
        assert removed is False
        assert service.get_user_interests(system.id, user.id)["player"] is False
        assert service.get_interested(system.id, "player") == []

    def test_toggle_interest_roles_are_independent(self, db_session):
        service = SystemService()
        system = SystemFactory(db_session)
        user = UserFactory(db_session)

        service.toggle_interest(system.id, user.id, "player")
        service.toggle_interest(system.id, user.id, "gm")

        interests = service.get_user_interests(system.id, user.id)
        assert interests == {"player": True, "gm": True}

    def test_toggle_interest_invalid_role(self, db_session):
        service = SystemService()
        system = SystemFactory(db_session)
        user = UserFactory(db_session)
        with pytest.raises(ValidationError):
            service.toggle_interest(system.id, user.id, "spectator")

    def test_toggle_interest_not_found(self, db_session):
        service = SystemService()
        user = UserFactory(db_session)
        with pytest.raises(NotFoundError):
            service.toggle_interest(-999, user.id, "player")
