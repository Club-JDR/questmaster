import pytest
from website.models import User
from website.repositories.user import UserRepository

from tests.constants import TEST_ADMIN_USER_ID


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
        user = User(id="100000000000000000", name="TestUser")
        repo.add(user)
        assert repo.get_by_id("100000000000000000") is not None

    def test_count(self, db_session):
        repo = UserRepository()
        assert repo.count() >= 2
