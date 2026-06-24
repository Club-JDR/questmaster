"""Admin routes for managing granular permissions (RBAC grants)."""

# Third-party imports
from flask import flash, redirect, render_template, request, session, url_for

# Local imports
from website.exceptions import DiscordAPIError, ValidationError
from website.models import PermissionGrant
from website.models.user import get_user_profile
from website.services.discord import DiscordService
from website.services.permission import PermissionService
from website.views.admin import admin_bp
from website.views.auth import require_permission

permission_service = PermissionService()
discord_service = DiscordService()


def _role_name_map(grants: list[PermissionGrant]) -> dict[str, str]:
    """Map Discord role IDs (used by role grants) to their role names.

    Fetches the guild roles once. Returns an empty map (callers fall back to the
    raw ID) if there are no role grants or Discord is unreachable.

    Args:
        grants: The grants being displayed.

    Returns:
        Mapping of role ID to role name.
    """
    if not any(g.subject_type == PermissionGrant.SUBJECT_ROLE for g in grants):
        return {}
    try:
        return {role["id"]: role["name"] for role in discord_service.list_roles()}
    except DiscordAPIError:
        return {}


def _subject_labels(grants: list[PermissionGrant]) -> dict[int, str]:
    """Resolve a human label (role/user name) for each grant's subject.

    Role names come from the guild role list; user names from the cached Discord
    profile lookup. Any unresolved subject falls back to its raw Discord ID.

    Args:
        grants: The grants being displayed.

    Returns:
        Mapping of grant id to a display label.
    """
    role_names = _role_name_map(grants)
    labels: dict[int, str] = {}
    for grant in grants:
        if grant.subject_type == PermissionGrant.SUBJECT_ROLE:
            labels[grant.id] = role_names.get(grant.subject_id, grant.subject_id)
        else:
            try:
                profile = get_user_profile(grant.subject_id)
                labels[grant.id] = profile.get("name") or grant.subject_id
            except Exception:  # noqa: BLE001 - best-effort name resolution
                labels[grant.id] = grant.subject_id
    return labels


@admin_bp.route("/permissions/", methods=["GET"])
@require_permission("permissions.manage")
def list_permissions():
    """Render the capability catalog with each capability's current grants."""
    grants = permission_service.list_grants()
    return render_template(
        "admin/permissions/list.html",
        catalog=permission_service.catalog(),
        grants_by_key=permission_service.grants_by_key(),
        subject_labels=_subject_labels(grants),
        subject_role=PermissionGrant.SUBJECT_ROLE,
        subject_user=PermissionGrant.SUBJECT_USER,
    )


@admin_bp.route("/permissions/grant", methods=["POST"])
@require_permission("permissions.manage")
def grant_permission():
    """Grant a capability to a Discord role or an individual user."""
    try:
        permission_service.grant(
            key=request.form.get("permission_key", ""),
            subject_type=request.form.get("subject_type", ""),
            subject_id=request.form.get("subject_id", ""),
            granted_by_id=session.get("user_id"),
        )
        flash("Permission accordée.", "success")
    except ValidationError:
        flash("Permission invalide ; vérifiez les champs saisis.", "danger")
    return redirect(url_for("admin.list_permissions"))


@admin_bp.route("/permissions/<int:grant_id>/revoke", methods=["POST"])
@require_permission("permissions.manage")
def revoke_permission(grant_id):
    """Revoke an existing grant."""
    permission_service.revoke(grant_id)
    flash("Permission révoquée.", "success")
    return redirect(url_for("admin.list_permissions"))
