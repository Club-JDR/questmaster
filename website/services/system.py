"""System service for game system business logic."""

from urllib.parse import urlparse

from config.constants import SYSTEM_INTEREST_ROLES
from website.exceptions import NotFoundError, ValidationError
from website.extensions import cache, db
from website.models import System, User, UserSystemInterest
from website.repositories.base import Pagination
from website.repositories.system import SystemRepository
from website.repositories.user_system_interest import UserSystemInterestRepository
from website.utils.logger import logger, sanitize_log_value


class SystemService:
    """Service layer for System (RPG game system) operations.

    Handles CRUD operations with cache invalidation, plus the system public
    page's lightweight matchmaking: who has run a system, who wants to run
    or play it, and the logged-in user's own declared interest.
    """

    def __init__(self, repository=None, interest_repository=None):
        self.repo = repository or SystemRepository()
        self.interest_repo = interest_repository or UserSystemInterestRepository()

    def _validate_reference_url(self, url: str | None) -> None:
        """Ensure a reference URL, if set, is a well-formed http(s) URL.

        Args:
            url: URL to validate, or None/empty (always valid).

        Raises:
            ValidationError: If set but not an absolute http(s) URL.
        """
        if not url:
            return
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValidationError(
                "reference_url must be an absolute http(s) URL.",
                field="reference_url",
                details={"value": url},
            )

    @cache.memoize()
    def get_all(self) -> list[System]:
        """Get all systems ordered by name.

        Returns:
            List of System instances.
        """
        return self.repo.get_all_ordered()

    def list_paginated(
        self, page: int = 1, per_page: int = 25, search: str | None = None
    ) -> Pagination:
        """Get a paginated, optionally searched, list of systems.

        Args:
            page: Page number (1-based).
            per_page: Items per page.
            search: Optional term matched against system ID and name.

        Returns:
            Pagination result of System instances.
        """
        return self.repo.paginate(page=page, per_page=per_page, search=search)

    def get_by_id(self, id: int) -> System:
        """Get system by ID.

        Args:
            id: System ID.

        Returns:
            System instance.

        Raises:
            NotFoundError: If system does not exist.
        """
        system = self.repo.get_by_id(id)
        if not system:
            raise NotFoundError(
                f"System with id {id} not found",
                resource_type="System",
                resource_id=id,
            )
        return system

    def create(
        self,
        name: str,
        icon: str = None,
        description: str = None,
        reference_url: str = None,
    ) -> System:
        """Create a new game system.

        Args:
            name: System name (must be unique).
            icon: Optional icon path.
            description: Optional Markdown blurb rendered on the system's public page.
            reference_url: Optional canonical external page for the system.

        Returns:
            Created System instance.

        Raises:
            ValidationError: If name already exists, or reference_url is malformed.
        """
        if self.repo.get_by_name(name):
            raise ValidationError("System name already exists.", field="name")
        self._validate_reference_url(reference_url)
        system = System(name=name, icon=icon, description=description, reference_url=reference_url)
        self.repo.add(system)
        db.session.commit()
        cache.delete_memoized(self.get_all)
        logger.info(f"System {system.id} created: {sanitize_log_value(name)}")
        return system

    def update(self, id: int, data: dict) -> System:
        """Update an existing system.

        Args:
            id: System ID.
            data: Dictionary of fields to update.

        Returns:
            Updated System instance.

        Raises:
            ValidationError: If reference_url is set and malformed.
        """
        system = self.repo.get_by_id_or_404(id)
        if "reference_url" in data:
            self._validate_reference_url(data["reference_url"])
        system.update_from_dict(data)
        db.session.commit()
        cache.delete_memoized(self.get_all)
        logger.info(f"System {id} updated")
        return system

    def delete(self, id: int) -> None:
        """Delete a system.

        Args:
            id: System ID.
        """
        system = self.repo.get_by_id_or_404(id)
        self.repo.delete(system)
        db.session.commit()
        cache.delete_memoized(self.get_all)
        logger.info(f"System {id} deleted")

    # -------------------------------------------------------------------
    # Public page: matchmaking lists + self-service interest toggle
    # -------------------------------------------------------------------

    def get_run_history(self, system_id: int) -> list[User]:
        """Get GMs who have actually run this system, from game history.

        Args:
            system_id: System ID.

        Returns:
            List of User instances, ordered by name.

        Raises:
            NotFoundError: If the system does not exist.
        """
        self.get_by_id(system_id)
        return self.repo.get_gm_history(system_id)

    def get_interested(self, system_id: int, role: str) -> list[UserSystemInterest]:
        """Get users who declared interest in a system for a given role.

        Args:
            system_id: System ID.
            role: "player" or "gm".

        Returns:
            List of UserSystemInterest instances, with ``user`` eager-loaded.

        Raises:
            NotFoundError: If the system does not exist.
            ValidationError: If role isn't a recognized interest role.
        """
        self.get_by_id(system_id)
        if role not in SYSTEM_INTEREST_ROLES:
            raise ValidationError("Invalid interest role.", field="role", details={"value": role})
        return self.interest_repo.list_by_system_and_role(system_id, role)

    def get_user_interests(self, system_id: int, user_id: str) -> dict[str, bool]:
        """Return whether the given user has declared interest, per role.

        Args:
            system_id: System ID.
            user_id: User ID.

        Returns:
            Dict keyed by role ("player", "gm"), values True/False.
        """
        return {
            role: self.interest_repo.get(user_id, system_id, role) is not None
            for role in SYSTEM_INTEREST_ROLES
        }

    def toggle_interest(
        self, system_id: int, user_id: str, role: str, note: str | None = None
    ) -> bool:
        """Add or remove a user's declared interest in a system for a role.

        Args:
            system_id: System ID.
            user_id: User ID.
            role: "player" or "gm".
            note: Optional free text, only used when adding a new interest.

        Returns:
            True if interest was added, False if an existing one was removed.

        Raises:
            NotFoundError: If the system does not exist.
            ValidationError: If role isn't a recognized interest role.
        """
        self.get_by_id(system_id)
        if role not in SYSTEM_INTEREST_ROLES:
            raise ValidationError("Invalid interest role.", field="role", details={"value": role})

        uid = sanitize_log_value(user_id)
        existing = self.interest_repo.get(user_id, system_id, role)
        if existing:
            self.interest_repo.delete(existing)
            db.session.commit()
            logger.info(f"User {uid} removed {role} interest in system {system_id}")
            return False

        interest = UserSystemInterest(user_id=user_id, system_id=system_id, role=role, note=note)
        self.interest_repo.add(interest)
        db.session.commit()
        logger.info(f"User {uid} declared {role} interest in system {system_id}")
        return True
