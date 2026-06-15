"""Admin routes for managing users."""

# Standard library imports
from datetime import datetime

# Third-party imports
from flask import flash, redirect, render_template, request, url_for

# Local imports
from website.exceptions import NotFoundError
from website.services.user import UserService
from website.views.admin import admin_bp

user_service = UserService()


@admin_bp.route("/users/", methods=["GET"])
def list_users():
    """List all users."""
    users = user_service.get_all()
    return render_template("admin/users/list.html", users=users)


@admin_bp.route("/users/<user_id>/edit", methods=["GET", "POST"])
def edit_user(user_id):
    """Edit an existing user (display name and activity status)."""
    try:
        user = user_service.get_by_id(user_id)
    except NotFoundError:
        flash("Utilisateur introuvable.", "danger")
        return redirect(url_for("admin.list_users"))

    if request.method == "POST":
        raw_date = request.form.get("not_player_as_of", "").strip()
        data = {
            "name": request.form.get("name", "").strip(),
            "not_player_as_of": datetime.fromisoformat(raw_date) if raw_date else None,
        }
        user_service.update(user_id, data)
        flash("Utilisateur mis à jour.", "success")
        return redirect(url_for("admin.list_users"))

    return render_template("admin/users/edit.html", user=user)
