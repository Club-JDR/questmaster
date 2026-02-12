import pytest
from website.models import SpecialEvent
from website.services.special_event import SpecialEventService
from website.exceptions import NotFoundError, ValidationError

from tests.factories import SpecialEventFactory


class TestSpecialEventService:
    def test_get_all(self, db_session):
        """Test get_all returns all events ordered by name."""
        service = SpecialEventService()
        SpecialEventFactory(db_session, name="Zebra Event", emoji="🦓", active=True)
        SpecialEventFactory(db_session, name="Alpha Event", emoji="🅰️", active=False)

        events = service.get_all()
        assert len(events) >= 2
        names = [e.name for e in events]
        assert names == sorted(names)

    def test_get_all_active_only(self, db_session):
        """Test get_all with active_only=True filters correctly."""
        service = SpecialEventService()
        SpecialEventFactory(
            db_session, name="Active Test Event", emoji="✅", active=True
        )
        SpecialEventFactory(
            db_session, name="Inactive Test Event", emoji="❌", active=False
        )

        active_events = service.get_all(active_only=True)
        active_names = [e.name for e in active_events]
        assert "Active Test Event" in active_names
        assert "Inactive Test Event" not in active_names

    def test_get_active(self, db_session):
        """Test get_active convenience method."""
        service = SpecialEventService()
        SpecialEventFactory(
            db_session, name="Active Convenience Event", emoji="✅", active=True
        )
        SpecialEventFactory(
            db_session, name="Inactive Convenience Event", emoji="❌", active=False
        )

        active_events = service.get_active()
        assert all(e.active for e in active_events)
        active_names = [e.name for e in active_events]
        assert "Active Convenience Event" in active_names

    def test_get_by_id(self, db_session):
        """Test get_by_id returns correct event."""
        service = SpecialEventService()
        event = SpecialEventFactory(
            db_session, name="Test Get Event", emoji="🔍", active=True
        )

        found = service.get_by_id(event.id)
        assert found.id == event.id
        assert found.name == "Test Get Event"

    def test_get_by_id_not_found(self, db_session):
        """Test get_by_id raises NotFoundError for nonexistent ID."""
        service = SpecialEventService()
        with pytest.raises(NotFoundError):
            service.get_by_id(-999)

    def test_create(self, db_session):
        """Test create method."""
        service = SpecialEventService()
        event = service.create(
            name="NewTestEvent", emoji="🎉", color=0x00FF00, active=True
        )
        assert event.id is not None
        assert event.name == "NewTestEvent"
        assert event.emoji == "🎉"
        assert event.color == 0x00FF00
        assert event.active is True

    def test_create_duplicate_name(self, db_session):
        """Test create raises ValidationError for duplicate name."""
        service = SpecialEventService()
        event1 = service.create(name="Duplicate Event", emoji="1️⃣")
        with pytest.raises(ValidationError) as exc_info:
            service.create(name="Duplicate Event", emoji="2️⃣")
        assert exc_info.value.field == "name"

    def test_update(self, db_session):
        """Test update method."""
        service = SpecialEventService()
        event = service.create(name="ToUpdate", emoji="📝", color=0xFF0000)
        updated = service.update(
            event.id,
            {"name": "Updated", "emoji": "✏️", "color": 0x0000FF, "active": True},
        )
        assert updated.name == "Updated"
        assert updated.emoji == "✏️"
        assert updated.color == 0x0000FF
        assert updated.active is True

    def test_update_duplicate_name(self, db_session):
        """Test update raises ValidationError when changing name to existing name."""
        service = SpecialEventService()
        event1 = service.create(name="Event One", emoji="1️⃣")
        event2 = service.create(name="Event Two", emoji="2️⃣")

        with pytest.raises(ValidationError) as exc_info:
            service.update(event2.id, {"name": "Event One"})
        assert exc_info.value.field == "name"

    def test_update_same_name_allowed(self, db_session):
        """Test update allows keeping the same name."""
        service = SpecialEventService()
        event = service.create(name="Same Name Event", emoji="📛")
        # Update other fields but keep the same name
        updated = service.update(event.id, {"name": "Same Name Event", "active": True})
        assert updated.name == "Same Name Event"
        assert updated.active is True

    def test_delete(self, db_session):
        """Test delete method."""
        service = SpecialEventService()
        event = service.create(name="ToDeleteService", emoji="🗑️")
        event_id = event.id

        service.delete(event_id)
        assert db_session.get(SpecialEvent, event_id) is None

    def test_delete_not_found(self, db_session):
        """Test delete raises 404 for nonexistent event."""
        from werkzeug.exceptions import NotFound

        service = SpecialEventService()
        with pytest.raises(NotFound):
            service.delete(-999)
