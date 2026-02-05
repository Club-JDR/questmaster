from website.models import Vtt
from website.repositories.base import BaseRepository


class VttRepository(BaseRepository[Vtt]):
    model_class = Vtt

    def get_all_ordered(self) -> list[Vtt]:
        return self.session.query(Vtt).order_by(Vtt.name).all()

    def get_by_name(self, name: str) -> Vtt | None:
        return self.session.query(Vtt).filter_by(name=name).first()
