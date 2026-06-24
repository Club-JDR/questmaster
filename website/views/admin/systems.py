"""Admin routes for managing game systems."""

# Third-party imports
from flask import flash, redirect, render_template, request, url_for

# Local imports
from config.constants import ADMIN_PAGE_SIZE
from website.exceptions import NotFoundError, ValidationError
from website.services.system import SystemService
from website.views.admin import admin_bp, get_list_params
from website.views.auth import require_permission

system_service = SystemService()


@admin_bp.route("/systems/", methods=["GET"])
@require_permission("system.manage")
def list_systems():
    """List game systems with search and pagination."""
    page, search = get_list_params()
    pagination = system_service.list_paginated(page=page, per_page=ADMIN_PAGE_SIZE, search=search)
    return render_template("admin/systems/list.html", pagination=pagination, search=search)


@admin_bp.route("/systems/new", methods=["GET", "POST"])
@require_permission("system.manage")
def create_system():
    """Create a new game system."""
    if request.method == "POST":
        try:
            system_service.create(
                name=request.form.get("name", "").strip(),
                icon=request.form.get("icon", "").strip() or None,
            )
            flash("Système créé.", "success")
            return redirect(url_for("admin.list_systems"))
        except ValidationError as e:
            flash(str(e), "danger")

    return render_template("admin/systems/form.html", system=None)


@admin_bp.route("/systems/<int:system_id>/edit", methods=["GET", "POST"])
@require_permission("system.manage")
def edit_system(system_id):
    """Edit an existing game system."""
    try:
        system = system_service.get_by_id(system_id)
    except NotFoundError:
        flash("Système introuvable.", "danger")
        return redirect(url_for("admin.list_systems"))

    if request.method == "POST":
        system_service.update(
            system_id,
            {
                "name": request.form.get("name", "").strip(),
                "icon": request.form.get("icon", "").strip() or None,
            },
        )
        flash("Système mis à jour.", "success")
        return redirect(url_for("admin.list_systems"))

    return render_template("admin/systems/form.html", system=system)


@admin_bp.route("/systems/<int:system_id>/delete", methods=["POST"])
@require_permission("system.manage")
def delete_system(system_id):
    """Delete a game system."""
    system_service.delete(system_id)
    flash("Système supprimé.", "success")
    return redirect(url_for("admin.list_systems"))
