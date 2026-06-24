"""Admin routes for managing trophies (badges) and user/trophy associations."""

# Third-party imports
from flask import flash, redirect, render_template, request, url_for

# Local imports
from config.constants import ADMIN_PAGE_SIZE
from website.exceptions import NotFoundError, ValidationError
from website.services.trophy import TrophyService
from website.services.user import UserService
from website.views.admin import admin_bp, get_list_params
from website.views.auth import require_permission

trophy_service = TrophyService()
user_service = UserService()


# --- Trophy definitions (Badges) -------------------------------------------


@admin_bp.route("/trophies/", methods=["GET"])
@require_permission("trophy.manage")
def list_trophies():
    """List trophy definitions (badges) with search and pagination."""
    page, search = get_list_params()
    pagination = trophy_service.list_paginated(page=page, per_page=ADMIN_PAGE_SIZE, search=search)
    return render_template("admin/trophies/list.html", pagination=pagination, search=search)


@admin_bp.route("/trophies/new", methods=["GET", "POST"])
@require_permission("trophy.manage")
def create_trophy():
    """Create a new trophy definition."""
    if request.method == "POST":
        try:
            trophy_service.create_trophy(
                name=request.form.get("name", "").strip(),
                unique="unique" in request.form,
                icon=request.form.get("icon", "").strip() or None,
            )
            flash("Badge créé.", "success")
            return redirect(url_for("admin.list_trophies"))
        except ValidationError as e:
            flash(str(e), "danger")

    return render_template("admin/trophies/form.html", trophy=None)


@admin_bp.route("/trophies/<int:trophy_id>/edit", methods=["GET", "POST"])
@require_permission("trophy.manage")
def edit_trophy(trophy_id):
    """Edit an existing trophy definition."""
    try:
        trophy = trophy_service.get_by_id(trophy_id)
    except NotFoundError:
        flash("Badge introuvable.", "danger")
        return redirect(url_for("admin.list_trophies"))

    if request.method == "POST":
        try:
            trophy_service.update_trophy(
                trophy_id,
                {
                    "name": request.form.get("name", "").strip(),
                    "unique": "unique" in request.form,
                    "icon": request.form.get("icon", "").strip() or None,
                },
            )
            flash("Badge mis à jour.", "success")
            return redirect(url_for("admin.list_trophies"))
        except ValidationError as e:
            flash(str(e), "danger")

    return render_template("admin/trophies/form.html", trophy=trophy)


@admin_bp.route("/trophies/<int:trophy_id>/delete", methods=["POST"])
@require_permission("trophy.manage")
def delete_trophy(trophy_id):
    """Delete a trophy definition."""
    trophy_service.delete_trophy(trophy_id)
    flash("Badge supprimé.", "success")
    return redirect(url_for("admin.list_trophies"))


# --- Per-user badges (user/trophy associations) ----------------------------


@admin_bp.route("/users/<user_id>/trophies", methods=["GET"])
@require_permission("trophy.manage")
def user_trophies(user_id):
    """List and manage a single user's badges."""
    try:
        user = user_service.get_by_id(user_id)
    except NotFoundError:
        flash("Utilisateur introuvable.", "danger")
        return redirect(url_for("admin.list_users"))

    owned = trophy_service.list_for_user(user_id)
    owned_ids = {ut.trophy_id for ut in owned}
    available = [t for t in trophy_service.get_all() if t.id not in owned_ids]
    return render_template(
        "admin/user_trophies/list.html",
        user=user,
        user_trophies=owned,
        available_trophies=available,
    )


@admin_bp.route("/users/<user_id>/trophies/award", methods=["POST"])
@require_permission("trophy.manage")
def award_user_trophy(user_id):
    """Award a badge to the user."""
    try:
        trophy_service.create_user_trophy(
            user_id=user_id,
            trophy_id=int(request.form.get("trophy_id")),
            quantity=int(request.form.get("quantity") or 1),
        )
        flash("Badge attribué.", "success")
    except (ValidationError, NotFoundError) as e:
        flash(str(e), "danger")
    return redirect(url_for("admin.user_trophies", user_id=user_id))


@admin_bp.route("/users/<user_id>/trophies/<int:trophy_id>/edit", methods=["POST"])
@require_permission("trophy.manage")
def edit_user_trophy(user_id, trophy_id):
    """Set the quantity of one of the user's badges."""
    try:
        trophy_service.update_user_trophy(
            user_id,
            trophy_id,
            quantity=int(request.form.get("quantity") or 1),
        )
        flash("Badge mis à jour.", "success")
    except NotFoundError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin.user_trophies", user_id=user_id))


@admin_bp.route("/users/<user_id>/trophies/<int:trophy_id>/delete", methods=["POST"])
@require_permission("trophy.manage")
def delete_user_trophy(user_id, trophy_id):
    """Remove one of the user's badges."""
    trophy_service.delete_user_trophy(user_id, trophy_id)
    flash("Badge retiré.", "success")
    return redirect(url_for("admin.user_trophies", user_id=user_id))


@admin_bp.route("/users/<user_id>/trophies/<int:trophy_id>/increment", methods=["POST"])
@require_permission("trophy.manage")
def increment_user_trophy(user_id, trophy_id):
    """Increment a (non-unique) trophy quantity by one."""
    try:
        trophy_service.award(user_id, trophy_id, amount=1)
        flash("Badge incrémenté.", "success")
    except NotFoundError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin.user_trophies", user_id=user_id))


@admin_bp.route("/users/<user_id>/trophies/<int:trophy_id>/decrement", methods=["POST"])
@require_permission("trophy.manage")
def decrement_user_trophy(user_id, trophy_id):
    """Decrement a trophy quantity by one, removing the row when it reaches zero."""
    try:
        trophy_service.decrement_user_trophy(user_id, trophy_id)
        flash("Badge décrémenté.", "success")
    except NotFoundError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin.user_trophies", user_id=user_id))
