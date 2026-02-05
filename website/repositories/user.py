from website.models import User
from website.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model_class = User
