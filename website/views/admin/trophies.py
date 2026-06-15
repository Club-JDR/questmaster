"""Admin routes for managing trophies (badges) and user/trophy associations."""

# Third-party imports
from flask import flash, redirect, render_template, request, url_for

# Local imports
from website.exceptions import NotFoundError, ValidationError
from website.services.trophy import TrophyService
from website.services.user import UserService
from website.views.admin import admin_bp

trophy_service = TrophyService()
user_service = UserService()


# --- Trophy definitions (Badges) -------------------------------------------


@admin_bp.route("/trophies/", methods=["GET"])
def list_trophies():
    """List all trophy definitions (badges)."""
    trophies = trophy_service.get_all()
    return render_template("admin/trophies/list.html", trophies=trophies)


@admin_bp.route("/trophies/new", methods=["GET", "POST"])
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
def delete_trophy(trophy_id):
    """Delete a trophy definition."""
    trophy_service.delete_trophy(trophy_id)
    flash("Badge supprimé.", "success")
    return redirect(url_for("admin.list_trophies"))


# --- User/trophy associations ----------------------------------------------


@admin_bp.route("/user-trophies/", methods=["GET"])
def list_user_trophies():
    """List all user/trophy associations."""
    user_trophies = trophy_service.get_all_user_trophies()
    return render_template("admin/user_trophies/list.html", user_trophies=user_trophies)


@admin_bp.route("/user-trophies/new", methods=["GET", "POST"])
def create_user_trophy():
    """Award a trophy to a user."""
    if request.method == "POST":
        try:
            trophy_service.create_user_trophy(
                user_id=request.form.get("user_id", "").strip(),
                trophy_id=int(request.form.get("trophy_id")),
                quantity=int(request.form.get("quantity") or 1),
            )
            flash("Badge attribué.", "success")
            return redirect(url_for("admin.list_user_trophies"))
        except (ValidationError, NotFoundError) as e:
            flash(str(e), "danger")

    return render_template(
        "admin/user_trophies/form.html",
        user_trophy=None,
        users=user_service.get_all(),
        trophies=trophy_service.get_all(),
    )


@admin_bp.route("/user-trophies/<user_id>/<int:trophy_id>/edit", methods=["GET", "POST"])
def edit_user_trophy(user_id, trophy_id):
    """Edit the quantity of a user/trophy association."""
    try:
        user_trophy = trophy_service.get_user_trophy(user_id, trophy_id)
    except NotFoundError:
        flash("Association introuvable.", "danger")
        return redirect(url_for("admin.list_user_trophies"))

    if request.method == "POST":
        trophy_service.update_user_trophy(
            user_id,
            trophy_id,
            quantity=int(request.form.get("quantity") or 1),
        )
        flash("Association mise à jour.", "success")
        return redirect(url_for("admin.list_user_trophies"))

    return render_template(
        "admin/user_trophies/form.html",
        user_trophy=user_trophy,
        users=user_service.get_all(),
        trophies=trophy_service.get_all(),
    )


@admin_bp.route("/user-trophies/<user_id>/<int:trophy_id>/delete", methods=["POST"])
def delete_user_trophy(user_id, trophy_id):
    """Remove a user/trophy association."""
    trophy_service.delete_user_trophy(user_id, trophy_id)
    flash("Association supprimée.", "success")
    return redirect(url_for("admin.list_user_trophies"))
