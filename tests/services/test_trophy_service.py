import uuid
import pytest
from website.models.trophy import Trophy, UserTrophy
from website.models.user import User
from website.services.trophy import TrophyService
from website.exceptions import NotFoundError


class TestTrophyService:
    def test_get_by_id(self, db_session):
        """Test get_by_id returns correct trophy."""
        service = TrophyService()
        trophy = Trophy(name="Test Get Trophy", unique=False, icon="🏆")
        db_session.add(trophy)
        db_session.commit()

        found = service.get_by_id(trophy.id)
        assert found.id == trophy.id
        assert found.name == "Test Get Trophy"

    def test_get_by_id_not_found(self, db_session):
        """Test get_by_id raises NotFoundError for nonexistent ID."""
        service = TrophyService()
        with pytest.raises(NotFoundError) as exc_info:
            service.get_by_id(-999)
        details = exc_info.value.details
        assert details["resource_type"] == "Trophy"
        assert details["resource_id"] == -999

    def test_get_all(self, db_session):
        """Test get_all returns all trophies."""
        service = TrophyService()
        trophy1 = Trophy(name="Trophy Alpha", unique=False)
        trophy2 = Trophy(name="Trophy Beta", unique=True)
        db_session.add(trophy1)
        db_session.add(trophy2)
        db_session.commit()

        trophies = service.get_all()
        assert len(trophies) >= 2
        names = [t.name for t in trophies]
        assert "Trophy Alpha" in names
        assert "Trophy Beta" in names

    def test_award_unique_trophy_first_time(self, db_session):
        """Test awarding a unique trophy for the first time."""
        service = TrophyService()

        # Create test data
        user = User(id="12345678901234567", name="Unique User 1")
        trophy = Trophy(name="Unique Award Trophy 1", unique=True, icon="🌟")
        db_session.add(user)
        db_session.add(trophy)
        db_session.commit()

        # Award unique trophy
        result = service.award(user.id, trophy.id, amount=5)
        assert result.quantity == 1  # Should be 1 regardless of amount

    def test_award_unique_trophy_second_time(self, db_session):
        """Test awarding a unique trophy a second time (should be idempotent)."""
        service = TrophyService()

        # Create test data
        user = User(id="22345678901234568", name="Unique User 2")
        trophy = Trophy(name="Unique Award Trophy 2", unique=True, icon="🌟")
        db_session.add(user)
        db_session.add(trophy)
        db_session.commit()

        user_trophy = UserTrophy(user_id=user.id, trophy_id=trophy.id, quantity=1)
        db_session.add(user_trophy)
        db_session.commit()

        # Try to award again - should remain at 1
        result = service.award(user.id, trophy.id, amount=10)
        assert result.quantity == 1

    def test_award_non_unique_trophy_creates_new(self, db_session):
        """Test awarding a non-unique trophy creates new record."""
        service = TrophyService()

        # Create test data
        user = User(id="32345678901234569", name="Non-Unique User 1")
        trophy = Trophy(name="Non-Unique Award Trophy 1", unique=False, icon="🎖️")
        db_session.add(user)
        db_session.add(trophy)
        db_session.commit()

        # Award non-unique trophy
        result = service.award(user.id, trophy.id, amount=7)
        assert result.quantity == 7

    def test_award_non_unique_trophy_increments(self, db_session):
        """Test awarding a non-unique trophy increments quantity."""
        service = TrophyService()

        # Create test data
        user = User(id="42345678901234570", name="Non-Unique User 2")
        trophy = Trophy(name="Non-Unique Award Trophy 2", unique=False, icon="🎖️")
        db_session.add(user)
        db_session.add(trophy)
        db_session.commit()

        user_trophy = UserTrophy(user_id=user.id, trophy_id=trophy.id, quantity=3)
        db_session.add(user_trophy)
        db_session.commit()

        # Award more
        result = service.award(user.id, trophy.id, amount=5)
        assert result.quantity == 8

    def test_award_nonexistent_trophy(self, db_session):
        """Test awarding a nonexistent trophy raises NotFoundError."""
        service = TrophyService()
        with pytest.raises(NotFoundError):
            service.award("52345678901234571", -999, amount=1)

    def test_get_leaderboard(self, db_session):
        """Test get_leaderboard returns sorted list."""
        service = TrophyService()

        # Create test data
        trophy = Trophy(name=f"Service Leaderboard Trophy {uuid.uuid4()}", unique=False)
        db_session.add(trophy)
        db_session.commit()

        users = [
            User(id="62345678901234572", name="Service Leader 1"),
            User(id="72345678901234573", name="Service Leader 2"),
        ]
        for user in users:
            db_session.add(user)
        db_session.commit()

        user_trophies = [
            UserTrophy(user_id="62345678901234572", trophy_id=trophy.id, quantity=15),
            UserTrophy(user_id="72345678901234573", trophy_id=trophy.id, quantity=30),
        ]
        for ut in user_trophies:
            db_session.add(ut)
        db_session.commit()

        # Get leaderboard
        leaderboard = service.get_leaderboard(trophy.id, limit=10)
        assert len(leaderboard) == 2
        assert leaderboard[0][0].id == "72345678901234573"  # Highest first
        assert leaderboard[0][1] == 30

    def test_get_leaderboard_nonexistent_trophy(self, db_session):
        """Test get_leaderboard raises NotFoundError for nonexistent trophy."""
        service = TrophyService()
        with pytest.raises(NotFoundError):
            service.get_leaderboard(-999, limit=10)

    def test_get_user_badges(self, db_session):
        """Test get_user_badges returns user's trophy summary."""
        service = TrophyService()

        # Create test data
        user = User(id="82345678901234574", name="Badge User")
        trophy1 = Trophy(name="Badge Trophy 1", unique=False, icon="🥇")
        trophy2 = Trophy(name="Badge Trophy 2", unique=True, icon="🥈")
        db_session.add(user)
        db_session.add(trophy1)
        db_session.add(trophy2)
        db_session.commit()

        user_trophy1 = UserTrophy(user_id=user.id, trophy_id=trophy1.id, quantity=10)
        user_trophy2 = UserTrophy(user_id=user.id, trophy_id=trophy2.id, quantity=1)
        db_session.add(user_trophy1)
        db_session.add(user_trophy2)
        db_session.commit()

        # Get badges
        badges = service.get_user_badges(user.id)
        assert len(badges) == 2

        # Check structure
        badge_names = [b["name"] for b in badges]
        assert "Badge Trophy 1" in badge_names
        assert "Badge Trophy 2" in badge_names

        for badge in badges:
            assert "name" in badge
            assert "icon" in badge
            assert "quantity" in badge

    def test_get_user_badges_no_trophies(self, db_session):
        """Test get_user_badges returns empty list for user with no trophies."""
        service = TrophyService()
        badges = service.get_user_badges("92345678901234575")
        assert badges == []
