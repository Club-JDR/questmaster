from website.exceptions import NotFoundError
from website.extensions import db
from website.models import User
from website.repositories.user import UserRepository


class UserService:
    def __init__(self, repository=None):
        self.repo = repository or UserRepository()

    def get_by_id(self, user_id: str) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(
                f"User with id {user_id} not found",
                resource_type="User",
                resource_id=user_id,
            )
        return user

    def get_or_create(self, user_id: str, name: str = "Inconnu") -> tuple[User, bool]:
        user = self.repo.get_by_id(user_id)
        if user:
            return user, False
        user = User(id=user_id, name=name)
        self.repo.add(user)
        db.session.commit()
        user.init_on_load()
        return user, True

    def get_all(self) -> list[User]:
        return self.repo.get_all()
