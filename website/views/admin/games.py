"""Admin routes for managing games (full field editor)."""

# Third-party imports
from flask import flash, redirect, render_template, request, url_for

# Local imports
from config.constants import (
    GAME_CHAR,
    GAME_FREQUENCIES,
    GAME_STATUS,
    GAME_TYPES,
    GAME_XP,
    RESTRICTIONS,
)
from website.exceptions import NotFoundError, ValidationError
from website.services.game import GameService
from website.services.special_event import SpecialEventService
from website.services.system import SystemService
from website.services.user import UserService
from website.services.vtt import VttService
from website.utils.form_parsers import get_ambience, get_classification, parse_restriction_tags
from website.views.admin import admin_bp

game_service = GameService()
system_service = SystemService()
vtt_service = VttService()
user_service = UserService()
special_event_service = SpecialEventService()


def _parse_game_form() -> dict:
    """Build a game-update dict from the submitted admin form.

    Returns:
        Dict of game fields ready for ``GameService.admin_update``.
    """
    return {
        "name": request.form.get("name", "").strip(),
        "slug": request.form.get("slug", "").strip(),
        "type": request.form.get("type"),
        "length": request.form.get("length", "").strip(),
        "gm_id": request.form.get("gm_id", "").strip(),
        "system_id": int(request.form["system_id"]),
        "vtt_id": int(request.form["vtt_id"]) if request.form.get("vtt_id") else None,
        "description": request.form.get("description", ""),
        "restriction": request.form.get("restriction"),
        "restriction_tags": parse_restriction_tags(request.form),
        "party_size": int(request.form.get("party_size") or 1),
        "party_selection": "party_selection" in request.form,
        "xp": request.form.get("xp") or None,
        "date": request.form.get("date"),
        "session_length": request.form.get("session_length"),
        "frequency": request.form.get("frequency") or None,
        "characters": request.form.get("characters") or None,
        "classification": get_classification(),
        "ambience": get_ambience(request.form),
        "complement": request.form.get("complement", "").strip() or None,
        "img": request.form.get("img", "").strip() or None,
        "channel": request.form.get("channel", "").strip() or None,
        "msg_id": request.form.get("msg_id", "").strip() or None,
        "role": request.form.get("role", "").strip() or None,
        "status": request.form.get("status"),
        "special_event_id": (
            int(request.form["special_event_id"]) if request.form.get("special_event_id") else None
        ),
    }


def _form_context() -> dict:
    """Reference data needed to render the game edit form.

    Returns:
        Dict of select-option sources and enum tuples.
    """
    return {
        "systems": system_service.get_all(),
        "vtts": vtt_service.get_all(),
        "users": user_service.get_all(),
        "special_events": special_event_service.get_all(),
        "game_types": GAME_TYPES,
        "restrictions": RESTRICTIONS,
        "xp_levels": GAME_XP,
        "characters": GAME_CHAR,
        "frequencies": GAME_FREQUENCIES,
        "statuses": GAME_STATUS,
    }


@admin_bp.route("/games/", methods=["GET"])
def list_games():
    """List all games."""
    games = game_service.list_all()
    return render_template("admin/games/list.html", games=games)


@admin_bp.route("/games/<int:game_id>/edit", methods=["GET", "POST"])
def edit_game(game_id):
    """Edit all fields of an existing game."""
    try:
        game = game_service.get_by_id(game_id)
    except NotFoundError:
        flash("Annonce introuvable.", "danger")
        return redirect(url_for("admin.list_games"))

    if request.method == "POST":
        try:
            game_service.admin_update(game_id, _parse_game_form())
            flash("Annonce mise à jour.", "success")
            return redirect(url_for("admin.list_games"))
        except ValidationError as e:
            flash(str(e), "danger")

    return render_template("admin/games/edit.html", game=game, **_form_context())


@admin_bp.route("/games/<int:game_id>/delete", methods=["POST"])
def delete_game(game_id):
    """Delete a game permanently (database only)."""
    game = game_service.get_by_id(game_id)
    game_service.delete(game.slug)
    flash("Annonce supprimée.", "success")
    return redirect(url_for("admin.list_games"))
