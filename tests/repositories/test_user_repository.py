from datetime import datetime

import pytest

from tests.constants import TEST_ADMIN_USER_ID
from tests.factories import UserFactory
from website.models import User
from website.repositories.user import UserRepository


class TestUserRepository:
    def test_get_by_id(self, db_session):
        repo = UserRepository()
        user = repo.get_by_id(TEST_ADMIN_USER_ID)
        assert user is not None
        assert user.id == TEST_ADMIN_USER_ID

    def test_get_by_id_not_found(self, db_session):
        repo = UserRepository()
        user = repo.get_by_id("000000000000000000")
        assert user is None

    def test_get_all(self, db_session):
        repo = UserRepository()
        users = repo.get_all()
        assert len(users) >= 2

    def test_add_and_rollback(self, db_session):
        repo = UserRepository()
        UserFactory(db_session, id="100000000000000000", name="TestUser")
        assert repo.get_by_id("100000000000000000") is not None

    def test_count(self, db_session):
        repo = UserRepository()
        assert repo.count() >= 2

    def test_get_active_users_excludes_inactive(self, db_session):
        repo = UserRepository()
        inactive_user = UserFactory(db_session, not_player_as_of=datetime(2025, 1, 1))
        active_users = repo.get_active_users()
        active_ids = [u.id for u in active_users]
        assert inactive_user.id not in active_ids

    def test_get_active_users_includes_active(self, db_session):
        repo = UserRepository()
        active_user = UserFactory(db_session)
        active_users = repo.get_active_users()
        active_ids = [u.id for u in active_users]
        assert active_user.id in active_ids

    def test_get_inactive_users(self, db_session):
        repo = UserRepository()
        inactive_user = UserFactory(db_session, not_player_as_of=datetime(2025, 1, 1))
        inactive_users = repo.get_inactive_users()
        inactive_ids = [u.id for u in inactive_users]
        assert inactive_user.id in inactive_ids

    def test_get_inactive_users_excludes_active(self, db_session):
        repo = UserRepository()
        active_user = UserFactory(db_session)
        inactive_users = repo.get_inactive_users()
        inactive_ids = [u.id for u in inactive_users]
        assert active_user.id not in inactive_ids
