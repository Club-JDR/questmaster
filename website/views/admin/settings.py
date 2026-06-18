"""Admin routes for managing runtime configuration overrides."""

# Third-party imports
from flask import flash, redirect, render_template, request, session, url_for

# Local imports
from website.exceptions import ValidationError
from website.services.setting import OVERRIDABLE_KEYS, SettingsService
from website.views.admin import admin_bp

settings_service = SettingsService()


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
    )
