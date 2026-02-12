"""Tests for TrophyRepository."""

from tests.factories import TrophyFactory, UserFactory, UserTrophyFactory
from website.models.trophy import UserTrophy
from website.repositories.trophy import TrophyRepository


class TestTrophyRepository:
    def test_get_user_trophy(self, db_session):
        """Test get_user_trophy returns correct record."""
        repo = TrophyRepository()

        user = UserFactory(db_session)
        trophy = TrophyFactory(db_session)
        UserTrophyFactory(db_session, user_id=user.id, trophy_id=trophy.id, quantity=5)

        found = repo.get_user_trophy(user.id, trophy.id)
        assert found is not None
        assert found.user_id == user.id
        assert found.trophy_id == trophy.id
        assert found.quantity == 5

    def test_get_user_trophy_not_found(self, db_session):
        """Test get_user_trophy returns None when not found."""
        repo = TrophyRepository()
        assert repo.get_user_trophy("99999999999999999", 999) is None

    def test_award_trophy_creates_new(self, db_session):
        """Test award_trophy creates new UserTrophy record."""
        repo = TrophyRepository()

        user = UserFactory(db_session)
        trophy = TrophyFactory(db_session)

        result = repo.award_trophy(user.id, trophy.id, amount=3)
        assert result is not None
        assert result.user_id == user.id
        assert result.trophy_id == trophy.id
        assert result.quantity == 3

        found = repo.get_user_trophy(user.id, trophy.id)
        assert found.quantity == 3

    def test_award_trophy_increments_existing(self, db_session):
        """Test award_trophy increments quantity for existing record."""
        repo = TrophyRepository()

        user = UserFactory(db_session)
        trophy = TrophyFactory(db_session)
        UserTrophyFactory(db_session, user_id=user.id, trophy_id=trophy.id, quantity=5)

        result = repo.award_trophy(user.id, trophy.id, amount=3)
        assert result.quantity == 8

        found = repo.get_user_trophy(user.id, trophy.id)
        assert found.quantity == 8

    def test_get_leaderboard(self, db_session):
        """Test get_leaderboard returns users sorted by trophy quantity."""
        repo = TrophyRepository()

        trophy = TrophyFactory(db_session)

        user1 = UserFactory(db_session, name="Leader 1")
        user2 = UserFactory(db_session, name="Leader 2")
        user3 = UserFactory(db_session, name="Leader 3")

        UserTrophyFactory(db_session, user_id=user1.id, trophy_id=trophy.id, quantity=10)
        UserTrophyFactory(db_session, user_id=user2.id, trophy_id=trophy.id, quantity=25)
        UserTrophyFactory(db_session, user_id=user3.id, trophy_id=trophy.id, quantity=5)

        leaderboard = repo.get_leaderboard(trophy.id, limit=10)
        assert len(leaderboard) == 3

        # Verify ordering (highest first)
        assert leaderboard[0][0].id == user2.id  # 25
        assert leaderboard[0][1] == 25
        assert leaderboard[1][0].id == user1.id  # 10
        assert leaderboard[1][1] == 10
        assert leaderboard[2][0].id == user3.id  # 5
        assert leaderboard[2][1] == 5

    def test_get_leaderboard_with_limit(self, db_session):
        """Test get_leaderboard respects limit parameter."""
        repo = TrophyRepository()

        trophy = TrophyFactory(db_session)

        users = [UserFactory(db_session, name=f"User {i}") for i in range(5)]
        for i, user in enumerate(users):
            UserTrophyFactory(db_session, user_id=user.id, trophy_id=trophy.id, quantity=i + 1)

        leaderboard = repo.get_leaderboard(trophy.id, limit=3)
        assert len(leaderboard) == 3

    def test_get_leaderboard_empty(self, db_session):
        """Test get_leaderboard returns empty list for trophy with no awards."""
        repo = TrophyRepository()

        trophy = TrophyFactory(db_session)

        leaderboard = repo.get_leaderboard(trophy.id, limit=10)
        assert leaderboard == []

    def test_inherits_get_by_id(self, db_session):
        """Test inherited get_by_id method works."""
        repo = TrophyRepository()
        trophy = TrophyFactory(db_session, name="TestTrophyGetById", unique=True)

        found = repo.get_by_id(trophy.id)
        assert found is not None
        assert found.id == trophy.id
        assert found.name == "TestTrophyGetById"

    def test_inherits_get_all(self, db_session):
        """Test inherited get_all method works."""
        repo = TrophyRepository()
        TrophyFactory(db_session, name="Trophy1")
        TrophyFactory(db_session, name="Trophy2", unique=True)

        all_trophies = repo.get_all()
        assert len(all_trophies) >= 2
        names = [t.name for t in all_trophies]
        assert "Trophy1" in names
        assert "Trophy2" in names
