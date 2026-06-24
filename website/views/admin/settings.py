"""Admin routes for managing runtime configuration overrides."""

# Third-party imports
from flask import flash, redirect, render_template, request, session, url_for

# Local imports
from config.constants import DASHBOARD_LIMIT_MAX, DISCORD_ROLE_LIMIT, GAMES_PER_PAGE_MAX
from website.exceptions import DiscordAPIError, ValidationError
from website.services.discord import DiscordService
from website.services.setting import OVERRIDABLE_KEYS, SettingsService
from website.utils.logger import logger
from website.views.admin import admin_bp

settings_service = SettingsService()
discord_service = DiscordService()


def _current_role_count() -> int | None:
    """Best-effort current guild role count for display, or None on failure."""
    try:
        return discord_service.count_roles_cached()
    except (DiscordAPIError, RuntimeError) as exc:
        logger.warning(f"Could not fetch guild role count: {exc}")
        return None


@admin_bp.route("/settings/", methods=["GET", "POST"])
def edit_settings():
    """Display and update database-backed configuration overrides.

    On POST, each overridable key is read from the form; an empty value clears
    the override so the key falls back to its environment value.
    """
    if request.method == "POST":
        values = {key: request.form.get(key, "") for key in OVERRIDABLE_KEYS}
        try:
            settings_service.set_many(values, updated_by_id=session.get("user_id"))
            flash("Paramètres mis à jour.", "success")
            return redirect(url_for("admin.edit_settings"))
        except ValidationError as e:
            flash(str(e), "danger")

    return render_template(
        "admin/settings/edit.html",
        settings=settings_service.get_effective(),
        direct_permissions_enabled=settings_service.is_direct_permissions_enabled(),
        role_auto_threshold=settings_service.get_role_auto_threshold(),
        role_count=_current_role_count(),
        role_limit=DISCORD_ROLE_LIMIT,
        dashboard_agenda_limit=settings_service.get_dashboard_agenda_limit(),
        dashboard_open_limit=settings_service.get_dashboard_open_limit(),
        dashboard_limit_max=DASHBOARD_LIMIT_MAX,
        games_per_page=settings_service.get_games_per_page(),
        games_per_page_max=GAMES_PER_PAGE_MAX,
    )


@admin_bp.route("/settings/permissions/", methods=["POST"])
def update_permissions_settings():
    """Update operational settings: direct-permission mode, dashboard sizes and page size."""
    enabled = "direct_permissions" in request.form
    updated_by = session.get("user_id")
    try:
        settings_service.set_role_auto_threshold(
            request.form.get("role_auto_threshold", ""), updated_by_id=updated_by
        )
        settings_service.set_direct_permissions(enabled, updated_by_id=updated_by)
        settings_service.set_dashboard_agenda_limit(
            request.form.get("dashboard_agenda_limit", ""), updated_by_id=updated_by
        )
        settings_service.set_dashboard_open_limit(
            request.form.get("dashboard_open_limit", ""), updated_by_id=updated_by
        )
        settings_service.set_games_per_page(
            request.form.get("games_per_page", ""), updated_by_id=updated_by
        )
        flash("Paramètres mis à jour.", "success")
    except ValidationError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin.edit_settings"))
