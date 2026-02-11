from website.models import SpecialEvent
from website.repositories.special_event import SpecialEventRepository


class TestSpecialEventRepository:
    def test_get_all_ordered(self, db_session):
        """Test that get_all returns events ordered by name."""
        repo = SpecialEventRepository()
        # Create test events
        event1 = SpecialEvent(name="Zebra Event", emoji="🦓", active=True)
        event2 = SpecialEvent(name="Alpha Event", emoji="🅰️", active=False)
        repo.add(event1)
        repo.add(event2)

        events = repo.get_all()
        assert len(events) >= 2
        names = [e.name for e in events]
        assert names == sorted(names)

    def test_get_all_active_only(self, db_session):
        """Test that get_all with active_only=True filters correctly."""
        repo = SpecialEventRepository()
        event1 = SpecialEvent(name="Active Event", emoji="✅", active=True)
        event2 = SpecialEvent(name="Inactive Event", emoji="❌", active=False)
        repo.add(event1)
        repo.add(event2)

        active_events = repo.get_all(active_only=True)
        assert all(e.active for e in active_events)
        assert any(e.name == "Active Event" for e in active_events)
        assert not any(e.name == "Inactive Event" for e in active_events)

    def test_get_active(self, db_session):
        """Test get_active convenience method."""
        repo = SpecialEventRepository()
        event1 = SpecialEvent(name="Active Event", emoji="✅", active=True)
        event2 = SpecialEvent(name="Inactive Event", emoji="❌", active=False)
        repo.add(event1)
        repo.add(event2)

        active_events = repo.get_active()
        assert all(e.active for e in active_events)
        assert any(e.name == "Active Event" for e in active_events)

    def test_get_by_name(self, db_session):
        """Test get_by_name returns correct event."""
        repo = SpecialEventRepository()
        event = SpecialEvent(name="Test Event", emoji="🎉", active=True)
        repo.add(event)

        found = repo.get_by_name("Test Event")
        assert found is not None
        assert found.name == "Test Event"
        assert found.emoji == "🎉"

    def test_get_by_name_not_found(self, db_session):
        """Test get_by_name returns None for nonexistent event."""
        repo = SpecialEventRepository()
        assert repo.get_by_name("nonexistent") is None

    def test_inherits_get_by_id(self, db_session):
        """Test inherited get_by_id method works."""
        repo = SpecialEventRepository()
        event = SpecialEvent(name="TestRepoGetById", emoji="🔍", active=True)
        added = repo.add(event)

        found = repo.get_by_id(added.id)
        assert found is not None
        assert found.id == added.id

    def test_inherits_add(self, db_session):
        """Test inherited add method works."""
        repo = SpecialEventRepository()
        new_event = SpecialEvent(
            name="TestRepoAdd", emoji="➕", color=0xFF0000, active=True
        )
        result = repo.add(new_event)
        assert result.id is not None
        assert result.name == "TestRepoAdd"
        assert result.color == 0xFF0000

    def test_inherits_delete(self, db_session):
        """Test inherited delete method works."""
        repo = SpecialEventRepository()
        new_event = SpecialEvent(name="TestRepoDelete", emoji="🗑️", active=False)
        repo.add(new_event)
        count_before = repo.count()

        repo.delete(new_event)
        assert repo.count() == count_before - 1
