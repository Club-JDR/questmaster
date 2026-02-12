import random

import pytest

from tests.constants import TEST_ADMIN_USER_ID
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
