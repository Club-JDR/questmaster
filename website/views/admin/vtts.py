"""Admin routes for managing virtual tabletops (VTTs)."""

# Third-party imports
from flask import flash, redirect, render_template, request, url_for

# Local imports
from config.constants import ADMIN_PAGE_SIZE
from website.exceptions import NotFoundError, ValidationError
from website.services.vtt import VttService
from website.views.admin import admin_bp, get_list_params

vtt_service = VttService()


@admin_bp.route("/vtts/", methods=["GET"])
def list_vtts():
    """List VTTs with search and pagination."""
    page, search = get_list_params()
    pagination = vtt_service.list_paginated(page=page, per_page=ADMIN_PAGE_SIZE, search=search)
    return render_template("admin/vtts/list.html", pagination=pagination, search=search)


@admin_bp.route("/vtts/new", methods=["GET", "POST"])
def create_vtt():
    """Create a new VTT."""
    if request.method == "POST":
        try:
            vtt_service.create(
                name=request.form.get("name", "").strip(),
                icon=request.form.get("icon", "").strip() or None,
            )
            flash("VTT créé.", "success")
            return redirect(url_for("admin.list_vtts"))
        except ValidationError as e:
            flash(str(e), "danger")

    return render_template("admin/vtts/form.html", vtt=None)


@admin_bp.route("/vtts/<int:vtt_id>/edit", methods=["GET", "POST"])
def edit_vtt(vtt_id):
    """Edit an existing VTT."""
    try:
        vtt = vtt_service.get_by_id(vtt_id)
    except NotFoundError:
        flash("VTT introuvable.", "danger")
        return redirect(url_for("admin.list_vtts"))

    if request.method == "POST":
        vtt_service.update(
            vtt_id,
            {
                "name": request.form.get("name", "").strip(),
                "icon": request.form.get("icon", "").strip() or None,
            },
        )
        flash("VTT mis à jour.", "success")
        return redirect(url_for("admin.list_vtts"))

    return render_template("admin/vtts/form.html", vtt=vtt)


@admin_bp.route("/vtts/<int:vtt_id>/delete", methods=["POST"])
def delete_vtt(vtt_id):
    """Delete a VTT."""
    vtt_service.delete(vtt_id)
    flash("VTT supprimé.", "success")
    return redirect(url_for("admin.list_vtts"))
