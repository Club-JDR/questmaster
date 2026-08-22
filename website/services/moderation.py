"""Moderation service for in-app infractions (warnings)."""

import logging

from config.constants import INFRACTION_SEVERITY_LABELS, INFRACTION_SEVERITY_REMINDER
from website.exceptions import NotFoundError, ValidationError
from website.extensions import db
from website.models import Infraction
from website.repositories.base import Pagination
from website.repositories.infraction import InfractionRepository
from website.repositories.user import UserRepository
from website.utils.logger import sanitize_log_value

logger = logging.getLogger(__name__)


class ModerationService:
    """Service layer for moderation infractions.

    Owns validation and the transaction boundary for creating, listing, and
    deleting infractions (warnings) issued against users.
    """

    def __init__(self, repository=None, user_repository=None):
        self.repo = repository or InfractionRepository()
        self.user_repo = user_repository or UserRepository()

    def list_paginated(
        self, page: int = 1, per_page: int = 25, search: str | None = None
    ) -> Pagination:
        """Return a paginated, optionally searched, list of infractions.

        Args:
            page: Page number (1-based).
            per_page: Items per page.
            search: Optional term matched against rule/reason/user.

        Returns:
            Pagination result of Infraction instances.
        """
        return self.repo.paginate(page=page, per_page=per_page, search=search)

    def list_for_user(self, user_id: str) -> list[Infraction]:
        """Return every infraction issued against a user, newest first.

        Args:
            user_id: Discord ID of the warned user.

        Returns:
            List of Infraction instances.
        """
        return self.repo.list_for_user(user_id)

    def get_by_id(self, infraction_id: int) -> Infraction:
        """Return an infraction by ID.

        Args:
            infraction_id: Primary key of the infraction.

        Returns:
            Infraction instance.

        Raises:
            NotFoundError: If no infraction has the given ID.
        """
        infraction = self.repo.get_by_id(infraction_id)
        if not infraction:
            raise NotFoundError(
                f"Infraction with id {infraction_id} not found",
                resource_type="Infraction",
                resource_id=infraction_id,
            )
        return infraction

    def create(self, user_id: str, data: dict) -> Infraction:
        """Create an infraction against a user.

        Args:
            user_id: Discord ID of the warned user (must exist).
            data: Infraction fields — ``reason`` (required), ``severity``
                (defaults to a reminder), ``rule_article``, ``message_link``,
                ``admin_id``, and ``created_at`` (optional issue date to
                backfill history; defaults to now).

        Returns:
            The created Infraction instance.

        Raises:
            ValidationError: If the reason is empty or the severity is unknown.
            NotFoundError: If the warned user does not exist.
        """
        reason = (data.get("reason") or "").strip()
        if not reason:
            raise ValidationError("A reason is required.", field="reason")
        severity = data.get("severity", INFRACTION_SEVERITY_REMINDER)
        if severity not in INFRACTION_SEVERITY_LABELS:
            raise ValidationError("Unknown severity level.", field="severity")
        if not self.user_repo.get_by_id(user_id):
            raise NotFoundError(
                f"User with id {user_id} not found",
                resource_type="User",
                resource_id=user_id,
            )

        infraction = Infraction(
            user_id=user_id,
            reason=reason,
            severity=severity,
            rule_article=(data.get("rule_article") or "").strip() or None,
            message_link=(data.get("message_link") or "").strip() or None,
            admin_id=data.get("admin_id"),
        )
        if data.get("created_at") is not None:
            infraction.created_at = data["created_at"]

        self.repo.add(infraction)
        db.session.commit()
        logger.info(
            f"Infraction {infraction.id} created for user "
            f"{sanitize_log_value(user_id)} (severity={severity})"
        )
        return infraction

    def update(self, infraction_id: int, data: dict) -> Infraction:
        """Update an existing infraction.

        Args:
            infraction_id: Primary key of the infraction to update.
            data: Fields to update (reason, severity, rule_article,
                message_link, created_at).

        Returns:
            The updated Infraction instance.

        Raises:
            NotFoundError: If the infraction does not exist.
            ValidationError: If a provided reason is empty or severity unknown.
        """
        infraction = self.get_by_id(infraction_id)

        if "reason" in data:
            reason = (data["reason"] or "").strip()
            if not reason:
                raise ValidationError("A reason is required.", field="reason")
            infraction.reason = reason
        if "severity" in data:
            severity = data["severity"]
            if severity not in INFRACTION_SEVERITY_LABELS:
                raise ValidationError("Unknown severity level.", field="severity")
            infraction.severity = severity
        if "rule_article" in data:
            infraction.rule_article = (data["rule_article"] or "").strip() or None
        if "message_link" in data:
            infraction.message_link = (data["message_link"] or "").strip() or None
        if "created_at" in data and data["created_at"] is not None:
            infraction.created_at = data["created_at"]

        db.session.commit()
        logger.info(f"Infraction {infraction_id} updated")
        return infraction

    def delete(self, infraction_id: int) -> None:
        """Delete an infraction.

        Args:
            infraction_id: Primary key of the infraction to remove.

        Raises:
            NotFoundError: If the infraction does not exist.
        """
        infraction = self.get_by_id(infraction_id)
        self.repo.delete(infraction)
        db.session.commit()
        logger.info(f"Infraction {infraction_id} deleted")
