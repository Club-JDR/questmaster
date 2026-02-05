from website.extensions import db, cache
from website.models import Vtt
from website.exceptions import NotFoundError, ValidationError
from website.repositories.vtt import VttRepository


class VttService:
    def __init__(self, repository=None):
        self.repo = repository or VttRepository()

    def get_all(self) -> list[Vtt]:
        return self.repo.get_all_ordered()

    def get_by_id(self, id: int) -> Vtt:
        vtt = self.repo.get_by_id(id)
        if not vtt:
            raise NotFoundError(
                f"Vtt with id {id} not found",
                resource_type="Vtt",
                resource_id=id,
            )
        return vtt

    def create(self, name: str, icon: str = None) -> Vtt:
        if self.repo.get_by_name(name):
            raise ValidationError("Vtt name already exists.", field="name")
        vtt = Vtt(name=name, icon=icon)
        self.repo.add(vtt)
        db.session.commit()
        cache.delete_memoized(Vtt.get_vtts)
        return vtt

    def update(self, id: int, data: dict) -> Vtt:
        vtt = self.repo.get_by_id_or_404(id)
        vtt.update_from_dict(data)
        db.session.commit()
        cache.delete_memoized(Vtt.get_vtts)
        return vtt

    def delete(self, id: int) -> None:
        vtt = self.repo.get_by_id_or_404(id)
        self.repo.delete(vtt)
        db.session.commit()
        cache.delete_memoized(Vtt.get_vtts)
