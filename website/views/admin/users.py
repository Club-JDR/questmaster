"""Admin routes for managing users."""

# Standard library imports
from datetime import datetime

# Third-party imports
from flask import flash, redirect, render_template, request, url_for

# Local imports
from config.constants import ADMIN_PAGE_SIZE
from website.exceptions import NotFoundError
from website.services.game import GameService
from website.services.user import UserService
from website.views.admin import admin_bp, get_list_params

user_service = UserService()
game_service = GameService()


@admin_bp.route("/users/", methods=["GET"])
def list_users():
    """List users with search and pagination."""
    page, search = get_list_params()
    pagination = user_service.list_paginated(page=page, per_page=ADMIN_PAGE_SIZE, search=search)
    return render_template("admin/users/list.html", pagination=pagination, search=search)


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


@admin_bp.route("/users/<user_id>/games", methods=["GET"])
def user_games(user_id):
    """List all games for a user, split by GM role and player role."""
    try:
        user = user_service.get_by_id(user_id)
    except NotFoundError:
        flash("Utilisateur introuvable.", "danger")
        return redirect(url_for("admin.list_users"))

    return render_template(
        "admin/users/games.html",
        user=user,
        gm_games=game_service.list_by_gm(user_id),
        player_games=game_service.list_by_player(user_id),
    )
