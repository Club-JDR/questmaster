import uuid
from website.models.trophy import Trophy, UserTrophy
from website.models.user import User
from website.repositories.trophy import TrophyRepository


class TestTrophyRepository:
    def test_get_user_trophy(self, db_session):
        """Test get_user_trophy returns correct record."""
        repo = TrophyRepository()

        # Create test data
        user = User(id="12345678901234567", name="Test User")
        trophy = Trophy(name="Test Trophy", unique=False)
        db_session.add(user)
        db_session.add(trophy)
        db_session.commit()

        user_trophy = UserTrophy(user_id=user.id, trophy_id=trophy.id, quantity=5)
        db_session.add(user_trophy)
        db_session.commit()

        # Test retrieval
        found = repo.get_user_trophy(user.id, trophy.id)
        assert found is not None
        assert found.user_id == user.id
        assert found.trophy_id == trophy.id
        assert found.quantity == 5

        # Cleanup
        db_session.delete(user_trophy)
        db_session.delete(trophy)
        db_session.delete(user)
        db_session.commit()

    def test_get_user_trophy_not_found(self, db_session):
        """Test get_user_trophy returns None when not found."""
        repo = TrophyRepository()
        assert repo.get_user_trophy("99999999999999999", 999) is None

    def test_award_trophy_creates_new(self, db_session):
        """Test award_trophy creates new UserTrophy record."""
        repo = TrophyRepository()

        # Create test data
        user = User(id="22345678901234568", name="Award User 1")
        trophy = Trophy(name="Award Trophy 1", unique=False)
        db_session.add(user)
        db_session.add(trophy)
        db_session.commit()

        # Award trophy
        result = repo.award_trophy(user.id, trophy.id, amount=3)
        assert result is not None
        assert result.user_id == user.id
        assert result.trophy_id == trophy.id
        assert result.quantity == 3

        # Verify in database
        found = repo.get_user_trophy(user.id, trophy.id)
        assert found.quantity == 3

        # Cleanup
        db_session.delete(result)
        db_session.delete(trophy)
        db_session.delete(user)
        db_session.commit()

    def test_award_trophy_increments_existing(self, db_session):
        """Test award_trophy increments quantity for existing record."""
        repo = TrophyRepository()

        # Create test data
        user = User(id="32345678901234569", name="Award User 2")
        trophy = Trophy(name="Award Trophy 2", unique=False)
        db_session.add(user)
        db_session.add(trophy)
        db_session.commit()

        user_trophy = UserTrophy(user_id=user.id, trophy_id=trophy.id, quantity=5)
        db_session.add(user_trophy)
        db_session.commit()

        # Award more
        result = repo.award_trophy(user.id, trophy.id, amount=3)
        assert result.quantity == 8

        # Verify in database
        found = repo.get_user_trophy(user.id, trophy.id)
        assert found.quantity == 8

        # Cleanup
        db_session.delete(user_trophy)
        db_session.delete(trophy)
        db_session.delete(user)
        db_session.commit()

    def test_get_leaderboard(self, db_session):
        """Test get_leaderboard returns users sorted by trophy quantity."""
        repo = TrophyRepository()

        # Create test data
        trophy = Trophy(name=f"Leaderboard Trophy {uuid.uuid4()}", unique=False)
        db_session.add(trophy)
        db_session.commit()

        users = [
            User(id="42345678901234570", name="Leader 1"),
            User(id="52345678901234571", name="Leader 2"),
            User(id="62345678901234572", name="Leader 3"),
        ]
        for user in users:
            db_session.add(user)
        db_session.commit()

        # Award different quantities
        user_trophies = [
            UserTrophy(user_id="42345678901234570", trophy_id=trophy.id, quantity=10),
            UserTrophy(user_id="52345678901234571", trophy_id=trophy.id, quantity=25),
            UserTrophy(user_id="62345678901234572", trophy_id=trophy.id, quantity=5),
        ]
        for ut in user_trophies:
            db_session.add(ut)
        db_session.commit()

        # Get leaderboard
        leaderboard = repo.get_leaderboard(trophy.id, limit=10)
        assert len(leaderboard) == 3

        # Verify ordering (highest first)
        assert leaderboard[0][0].id == "52345678901234571"  # 25
        assert leaderboard[0][1] == 25
        assert leaderboard[1][0].id == "42345678901234570"  # 10
        assert leaderboard[1][1] == 10
        assert leaderboard[2][0].id == "62345678901234572"  # 5
        assert leaderboard[2][1] == 5

        # Cleanup
        for ut in user_trophies:
            db_session.delete(ut)
        for user in users:
            db_session.delete(user)
        db_session.delete(trophy)
        db_session.commit()

    def test_get_leaderboard_with_limit(self, db_session):
        """Test get_leaderboard respects limit parameter."""
        repo = TrophyRepository()

        # Create test data
        trophy = Trophy(name=f"Limited Leaderboard Trophy {uuid.uuid4()}", unique=False)
        db_session.add(trophy)
        db_session.commit()

        users = [
            User(id=f"{72345678901234570 + i}", name=f"User {i}") for i in range(5)
        ]
        for user in users:
            db_session.add(user)
        db_session.commit()

        user_trophies = [
            UserTrophy(user_id=user.id, trophy_id=trophy.id, quantity=i + 1)
            for i, user in enumerate(users)
        ]
        for ut in user_trophies:
            db_session.add(ut)
        db_session.commit()

        # Get limited leaderboard
        leaderboard = repo.get_leaderboard(trophy.id, limit=3)
        assert len(leaderboard) == 3

        # Cleanup
        for ut in user_trophies:
            db_session.delete(ut)
        for user in users:
            db_session.delete(user)
        db_session.delete(trophy)
        db_session.commit()

    def test_get_leaderboard_empty(self, db_session):
        """Test get_leaderboard returns empty list for trophy with no awards."""
        repo = TrophyRepository()

        # Create trophy but no awards
        trophy = Trophy(name="Empty Leaderboard Trophy", unique=False)
        db_session.add(trophy)
        db_session.commit()

        leaderboard = repo.get_leaderboard(trophy.id, limit=10)
        assert leaderboard == []

        # Cleanup
        db_session.delete(trophy)
        db_session.commit()

    def test_inherits_get_by_id(self, db_session):
        """Test inherited get_by_id method works."""
        repo = TrophyRepository()
        trophy = Trophy(name="TestTrophyGetById", unique=True, icon="🏆")
        added = repo.add(trophy)

        found = repo.get_by_id(added.id)
        assert found is not None
        assert found.id == added.id
        assert found.name == "TestTrophyGetById"

        db_session.rollback()

    def test_inherits_get_all(self, db_session):
        """Test inherited get_all method works."""
        repo = TrophyRepository()
        trophy1 = Trophy(name="Trophy1", unique=False)
        trophy2 = Trophy(name="Trophy2", unique=True)
        repo.add(trophy1)
        repo.add(trophy2)

        all_trophies = repo.get_all()
        assert len(all_trophies) >= 2
        names = [t.name for t in all_trophies]
        assert "Trophy1" in names
        assert "Trophy2" in names

        db_session.rollback()
