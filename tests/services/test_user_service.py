import random
from datetime import datetime

import pytest

from tests.constants import TEST_ADMIN_USER_ID
from tests.factories import UserFactory
from website.exceptions import NotFoundError
from website.models import User
from website.services.user import UserService


class TestUserService:
    def test_get_by_id(self, db_session):
        service = UserService()
        user = service.get_by_id(TEST_ADMIN_USER_ID)
        assert user is not None
        assert user.id == TEST_ADMIN_USER_ID

    def test_get_by_id_not_found(self, db_session):
        service = UserService()
        with pytest.raises(NotFoundError):
            service.get_by_id("000000000000000000")

    def test_get_all(self, db_session):
        service = UserService()
        users = service.get_all()
        assert len(users) >= 2

    def test_get_or_create_existing(self, db_session):
        service = UserService()
        user, created = service.get_or_create(TEST_ADMIN_USER_ID)
        assert user is not None
        assert created is False

    def test_get_or_create_new(self, db_session):
        user_id = str(random.randint(10**17, 10**18 - 1))
        service = UserService()
        user, created = service.get_or_create(user_id, name="NewTestUser")
        assert user is not None
        assert user.id == user_id
        assert created is True
        # Verify it persists
        found = db_session.get(User, user_id)
        assert found is not None

    def test_get_active_users_excludes_inactive(self, db_session):
        inactive_user = UserFactory(db_session, not_player_as_of=datetime(2025, 1, 1))
        service = UserService()
        active_users = service.get_active_users()
        active_ids = [u.id for u in active_users]
        assert inactive_user.id not in active_ids

    def test_get_inactive_users(self, db_session):
        inactive_user = UserFactory(db_session, not_player_as_of=datetime(2025, 1, 1))
        service = UserService()
        inactive_users = service.get_inactive_users()
        inactive_ids = [u.id for u in inactive_users]
        assert inactive_user.id in inactive_ids

    def test_get_active_user_ids(self, db_session):
        active_user = UserFactory(db_session)
        inactive_user = UserFactory(db_session, not_player_as_of=datetime(2025, 1, 1))
        service = UserService()
        ids = service.get_active_user_ids()
        assert active_user.id in ids
        assert inactive_user.id not in ids

    def test_get_inactive_user_ids(self, db_session):
        active_user = UserFactory(db_session)
        inactive_user = UserFactory(db_session, not_player_as_of=datetime(2025, 1, 1))
        service = UserService()
        ids = service.get_inactive_user_ids()
        assert inactive_user.id in ids
        assert active_user.id not in ids

    def test_get_by_ids(self, db_session):
        user1 = UserFactory(db_session)
        user2 = UserFactory(db_session)
        service = UserService()
        results = service.get_by_ids([user1.id, user2.id])
        result_ids = [u.id for u in results]
        assert user1.id in result_ids
        assert user2.id in result_ids

    def test_mark_inactive(self, db_session):
        user = UserFactory(db_session)
        service = UserService()
        result = service.mark_inactive(user.id)
        assert result.not_player_as_of is not None

    def test_clear_inactive(self, db_session):
        user = UserFactory(db_session, not_player_as_of=datetime(2025, 1, 1))
        service = UserService()
        result = service.clear_inactive(user.id)
        assert result.not_player_as_of is None

    def test_persist_profile_writes_name_to_db(self, db_session):
        """persist_profile must actually update the stored name (not a no-op).

        Reads the raw column to bypass User.init_on_load, which resolves the
        display name at load time and previously masked the missing write.
        """
        user = UserFactory(db_session, name="Inconnu")
        service = UserService()

        service.persist_profile(
            user.id, {"name": "RealName", "avatar": "/a.png", "username": "realname"}
        )

        stored = db_session.query(User.name, User.username).filter(User.id == user.id).one()
        assert stored.name == "RealName"
        assert stored.username == "realname"

    def test_search_matches_username(self, db_session):
        user = UserFactory(db_session, name="Display", username="zsearch-handle")
        service = UserService()
        results = service.search("zsearch-handle")
        assert user.id in [u.id for u in results]

    def test_search_matches_name(self, db_session):
        user = UserFactory(db_session, name="ZsearchDisplayName", username="other")
        service = UserService()
        results = service.search("ZsearchDisplayName")
        assert user.id in [u.id for u in results]

    def test_search_matches_id(self, db_session):
        user = UserFactory(db_session)
        service = UserService()
        results = service.search(user.id)
        assert user.id in [u.id for u in results]

    def test_search_blank_returns_empty(self, db_session):
        service = UserService()
        assert service.search("") == []
        assert service.search("   ") == []

    def test_search_respects_limit(self, db_session):
        for _ in range(5):
            UserFactory(db_session, name="ZlimitUser", username=f"zlimit-{random.random()}")
        service = UserService()
        results = service.search("ZlimitUser", limit=3)
        assert len(results) <= 3

    def test_resolve_input_numeric_id(self, db_session):
        user_id = str(random.randint(10**17, 10**18 - 1))
        service = UserService()
        resolved = service.resolve_input(user_id)
        assert resolved is not None
        assert resolved.id == user_id

    def test_resolve_input_unique_username(self, db_session):
        user = UserFactory(db_session, name="Whoever", username="zresolve-unique")
        service = UserService()
        resolved = service.resolve_input("zresolve-unique")
        assert resolved is not None
        assert resolved.id == user.id

    def test_resolve_input_ambiguous_returns_none(self, db_session):
        UserFactory(db_session, name="ZambiguousName", username="zamb-1")
        UserFactory(db_session, name="ZambiguousName", username="zamb-2")
        service = UserService()
        assert service.resolve_input("ZambiguousName") is None

    def test_resolve_input_strips_at_and_whitespace(self, db_session):
        user = UserFactory(db_session, name="Atuser", username="zatuser-handle")
        service = UserService()
        resolved = service.resolve_input("  @zatuser-handle  ")
        assert resolved is not None
        assert resolved.id == user.id

    def test_resolve_input_empty_returns_none(self, db_session):
        service = UserService()
        assert service.resolve_input("") is None
        assert service.resolve_input("   @ ") is None

    def test_persist_profile_reactivate_clears_flag(self, db_session):
        """persist_profile(reactivate=True) clears the inactive flag and sets name."""
        user = UserFactory(db_session, name="Inconnu", not_player_as_of=datetime(2025, 1, 1))
        service = UserService()

        service.persist_profile(user.id, {"name": "Back", "avatar": "/a.png"}, reactivate=True)

        stored = (
            db_session.query(User.name, User.not_player_as_of).filter(User.id == user.id).one()
        )
        assert stored.name == "Back"
        assert stored.not_player_as_of is None
