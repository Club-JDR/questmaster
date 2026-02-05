from website.models import System
from website.repositories.base import BaseRepository


class SystemRepository(BaseRepository[System]):
    model_class = System

    def get_all_ordered(self) -> list[System]:
        return self.session.query(System).order_by(System.name).all()

    def get_by_name(self, name: str) -> System | None:
        return self.session.query(System).filter_by(name=name).first()
