from website.exceptions import NotFoundError, ValidationError
from website.extensions import cache, db
from website.models import System
from website.repositories.system import SystemRepository


class SystemService:
    def __init__(self, repository=None):
        self.repo = repository or SystemRepository()

    def get_all(self) -> list[System]:
        return self.repo.get_all_ordered()

    def get_by_id(self, id: int) -> System:
        system = self.repo.get_by_id(id)
        if not system:
            raise NotFoundError(
                f"System with id {id} not found",
                resource_type="System",
                resource_id=id,
            )
        return system

    def create(self, name: str, icon: str = None) -> System:
        if self.repo.get_by_name(name):
            raise ValidationError("System name already exists.", field="name")
        system = System(name=name, icon=icon)
        self.repo.add(system)
        db.session.commit()
        cache.delete_memoized(System.get_systems)
        return system

    def update(self, id: int, data: dict) -> System:
        system = self.repo.get_by_id_or_404(id)
        system.update_from_dict(data)
        db.session.commit()
        cache.delete_memoized(System.get_systems)
        return system

    def delete(self, id: int) -> None:
        system = self.repo.get_by_id_or_404(id)
        self.repo.delete(system)
        db.session.commit()
        cache.delete_memoized(System.get_systems)
