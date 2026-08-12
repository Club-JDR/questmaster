"""Admin routes for in-app moderation infractions."""

# Standard library imports
from datetime import datetime

# Third-party imports
from flask import flash, redirect, render_template, request, session, url_for

# Local imports
from config.constants import (
    ADMIN_PAGE_SIZE,
    INFRACTION_SEVERITY_LABELS,
    INFRACTION_SEVERITY_REMINDER,
)
from website.exceptions import NotFoundError, ValidationError
from website.services.moderation import ModerationService
from website.services.user import UserService
from website.views.admin import admin_bp, get_list_params
from website.views.auth import require_permission

moderation_service = ModerationService()
user_service = UserService()


def _parse_created_at(raw: str | None) -> datetime | None:
    """Parse an ISO datetime/date string from the form, or None.

    Args:
        raw: Raw value from the form (``datetime-local`` or date), or None.

    Returns:
        Parsed datetime, or None if no value was provided.
    """
    raw = (raw or "").strip()
    if not raw:
        return None
    return datetime.fromisoformat(raw)


def _parse_severity(raw: str | None) -> int:
    """Parse a severity value from the form, defaulting to a reminder.

    Args:
        raw: Raw severity value from the form.

    Returns:
        Integer severity (defaults to reminder when absent/invalid-int).
    """
    try:
        return int(raw)
    except (TypeError, ValueError):
        return INFRACTION_SEVERITY_REMINDER


@admin_bp.route("/infractions/", methods=["GET"])
@require_permission("moderation.manage")
def list_infractions():
    """List all infractions with search and pagination."""
    page, search = get_list_params()
    pagination = moderation_service.list_paginated(
        page=page, per_page=ADMIN_PAGE_SIZE, search=search
    )
    return render_template(
        "admin/infractions/list.html",
        pagination=pagination,
        search=search,
        severity_labels=INFRACTION_SEVERITY_LABELS,
    )


@admin_bp.route("/infractions/user/<user_id>", methods=["GET", "POST"])
@require_permission("moderation.manage")
def user_infractions(user_id):
    """Show a user's infractions and create a new one against them."""
    try:
        user = user_service.get_by_id(user_id)
    except NotFoundError:
        flash("Utilisateur introuvable.", "danger")
        return redirect(url_for("admin.list_infractions"))

    if request.method == "POST":
        try:
            moderation_service.create(
                user_id=user.id,
                reason=request.form.get("reason", ""),
                severity=_parse_severity(request.form.get("severity")),
                rule_article=request.form.get("rule_article"),
                message_link=request.form.get("message_link"),
                admin_id=session.get("user_id"),
                created_at=_parse_created_at(request.form.get("created_at")),
            )
            flash("Infraction enregistrée.", "success")
            return redirect(url_for("admin.user_infractions", user_id=user.id))
        except ValidationError as e:
            flash(str(e), "danger")

    return render_template(
        "admin/infractions/user.html",
        user=user,
        infractions=moderation_service.list_for_user(user.id),
        severity_labels=INFRACTION_SEVERITY_LABELS,
    )


@admin_bp.route("/infractions/<int:infraction_id>/edit", methods=["GET", "POST"])
@require_permission("moderation.manage")
def edit_infraction(infraction_id):
    """Edit an existing infraction."""
    try:
        infraction = moderation_service.get_by_id(infraction_id)
    except NotFoundError:
        flash("Infraction introuvable.", "danger")
        return redirect(url_for("admin.list_infractions"))

    if request.method == "POST":
        try:
            moderation_service.update(
                infraction_id,
                {
                    "reason": request.form.get("reason", ""),
                    "severity": _parse_severity(request.form.get("severity")),
                    "rule_article": request.form.get("rule_article"),
                    "message_link": request.form.get("message_link"),
                    "created_at": _parse_created_at(request.form.get("created_at")),
                },
            )
            flash("Infraction mise à jour.", "success")
            return redirect(url_for("admin.user_infractions", user_id=infraction.user_id))
        except ValidationError as e:
            flash(str(e), "danger")

    return render_template(
        "admin/infractions/form.html",
        infraction=infraction,
        severity_labels=INFRACTION_SEVERITY_LABELS,
    )


@admin_bp.route("/infractions/<int:infraction_id>/delete", methods=["POST"])
@require_permission("moderation.manage")
def delete_infraction(infraction_id):
    """Delete an infraction."""
    try:
        infraction = moderation_service.get_by_id(infraction_id)
    except NotFoundError:
        flash("Infraction introuvable.", "danger")
        return redirect(url_for("admin.list_infractions"))

    user_id = infraction.user_id
    moderation_service.delete(infraction_id)
    flash("Infraction supprimée.", "success")
    return redirect(url_for("admin.user_infractions", user_id=user_id))
