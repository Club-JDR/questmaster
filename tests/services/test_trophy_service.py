"""Tests for TrophyService."""

import pytest

from website.models.trophy import UserTrophy
from website.services.trophy import TrophyService
from website.exceptions import NotFoundError

from tests.factories import TrophyFactory, UserFactory, UserTrophyFactory


class TestTrophyService:
    def test_get_by_id(self, db_session):
        """Test get_by_id returns correct trophy."""
        service = TrophyService()
        trophy = TrophyFactory(db_session, name="Test Get Trophy", icon="icon.png")

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
        TrophyFactory(db_session, name="Trophy Alpha")
        TrophyFactory(db_session, name="Trophy Beta", unique=True)

        trophies = service.get_all()
        assert len(trophies) >= 2
        names = [t.name for t in trophies]
        assert "Trophy Alpha" in names
        assert "Trophy Beta" in names

    def test_award_unique_trophy_first_time(self, db_session):
        """Test awarding a unique trophy for the first time."""
        service = TrophyService()

        user = UserFactory(db_session)
        trophy = TrophyFactory(db_session, unique=True)

        result = service.award(user.id, trophy.id, amount=5)
        assert result.quantity == 1  # Should be 1 regardless of amount

    def test_award_unique_trophy_second_time(self, db_session):
        """Test awarding a unique trophy a second time (should be idempotent)."""
        service = TrophyService()

        user = UserFactory(db_session)
        trophy = TrophyFactory(db_session, unique=True)
        UserTrophyFactory(db_session, user_id=user.id, trophy_id=trophy.id, quantity=1)

        # Try to award again - should remain at 1
        result = service.award(user.id, trophy.id, amount=10)
        assert result.quantity == 1

    def test_award_non_unique_trophy_creates_new(self, db_session):
        """Test awarding a non-unique trophy creates new record."""
        service = TrophyService()

        user = UserFactory(db_session)
        trophy = TrophyFactory(db_session)

        result = service.award(user.id, trophy.id, amount=7)
        assert result.quantity == 7

    def test_award_non_unique_trophy_increments(self, db_session):
        """Test awarding a non-unique trophy increments quantity."""
        service = TrophyService()

        user = UserFactory(db_session)
        trophy = TrophyFactory(db_session)
        UserTrophyFactory(db_session, user_id=user.id, trophy_id=trophy.id, quantity=3)

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

        trophy = TrophyFactory(db_session)

        user1 = UserFactory(db_session, name="Service Leader 1")
        user2 = UserFactory(db_session, name="Service Leader 2")

        UserTrophyFactory(
            db_session, user_id=user1.id, trophy_id=trophy.id, quantity=15
        )
        UserTrophyFactory(
            db_session, user_id=user2.id, trophy_id=trophy.id, quantity=30
        )

        leaderboard = service.get_leaderboard(trophy.id, limit=10)
        assert len(leaderboard) == 2
        assert leaderboard[0][0].id == user2.id  # Highest first
        assert leaderboard[0][1] == 30

    def test_get_leaderboard_nonexistent_trophy(self, db_session):
        """Test get_leaderboard raises NotFoundError for nonexistent trophy."""
        service = TrophyService()
        with pytest.raises(NotFoundError):
            service.get_leaderboard(-999, limit=10)

    def test_get_user_badges(self, db_session):
        """Test get_user_badges returns user's trophy summary."""
        service = TrophyService()

        user = UserFactory(db_session, name="Badge User")
        trophy1 = TrophyFactory(db_session, name="Badge Trophy 1", icon="icon1.png")
        trophy2 = TrophyFactory(
            db_session, name="Badge Trophy 2", unique=True, icon="icon2.png"
        )

        UserTrophyFactory(
            db_session, user_id=user.id, trophy_id=trophy1.id, quantity=10
        )
        UserTrophyFactory(
            db_session, user_id=user.id, trophy_id=trophy2.id, quantity=1
        )

        badges = service.get_user_badges(user.id)
        assert len(badges) == 2

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
