"""Admin routes for managing games (full field editor)."""

# Third-party imports
from flask import flash, redirect, render_template, request, session, url_for

# Local imports
from config.constants import (
    ADMIN_PAGE_SIZE,
    GAME_CHAR,
    GAME_FREQUENCIES,
    GAME_STATUS,
    GAME_TYPES,
    GAME_XP,
    RESTRICTIONS,
)
from website.exceptions import (
    DuplicateRegistrationError,
    NotFoundError,
    TrophiesAlreadyAwardedError,
    TrophiesNotAwardedError,
    TrophyAwardFailedError,
    ValidationError,
)
from website.services.game import GameService
from website.services.special_event import SpecialEventService
from website.services.system import SystemService
from website.services.user import UserService
from website.services.vtt import VttService
from website.utils.form_parsers import get_ambience, get_classification, parse_restriction_tags
from website.views.admin import admin_bp, get_list_params
from website.views.auth import admin_only

game_service = GameService()
system_service = SystemService()
vtt_service = VttService()
user_service = UserService()
special_event_service = SpecialEventService()

_GAME_NOT_FOUND_MESSAGE = "Annonce introuvable."
_EDIT_GAME_ENDPOINT = "admin.edit_game"

_VALIDATION_MESSAGES_BY_FIELD = {
    "user_id": "Cette personne n'est pas inscrite à cette partie.",
}


def _flash_validation_error(error: ValidationError) -> None:
    """Flash a French message for a ``GameService`` validation failure.

    Args:
        error: The English domain exception raised by the service.
    """
    message = _VALIDATION_MESSAGES_BY_FIELD.get(
        error.field, "Les informations saisies sont invalides."
    )
    flash(message, "danger")


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
        "open_to_viewers": "open_to_viewers" in request.form,
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
@admin_only
def list_games():
    """List games with search and pagination."""
    page, search = get_list_params()
    pagination = game_service.list_paginated(page=page, per_page=ADMIN_PAGE_SIZE, search=search)
    return render_template("admin/games/list.html", pagination=pagination, search=search)


@admin_bp.route("/games/<int:game_id>/edit", methods=["GET", "POST"])
@admin_only
def edit_game(game_id):
    """Edit all fields of an existing game."""
    try:
        game = game_service.get_by_id(game_id)
    except NotFoundError:
        flash(_GAME_NOT_FOUND_MESSAGE, "danger")
        return redirect(url_for("admin.list_games"))

    if request.method == "POST":
        try:
            game_service.admin_update(game_id, _parse_game_form())
            flash("Annonce mise à jour.", "success")
            return redirect(url_for("admin.list_games"))
        except ValidationError as e:
            _flash_validation_error(e)

    viewers = game_service.list_viewers(game.id)
    return render_template("admin/games/edit.html", game=game, viewers=viewers, **_form_context())


@admin_bp.route("/games/<int:game_id>/players/add", methods=["POST"])
@admin_only
def add_game_player(game_id):
    """Add a player to a game by Discord ID (admin roster management).

    Mirrors the public "Gérer" modal's add-player flow: the target must hold
    the Discord player role. The registration is forced (bypasses
    capacity/status/schedule checks), the trusted admin override.
    """
    uid = request.form.get("discord_id", "").strip()
    if not uid:
        flash("Identifiant Discord manquant.", "danger")
        return redirect(url_for(_EDIT_GAME_ENDPOINT, game_id=game_id))

    try:
        game = game_service.get_by_id(game_id)
        user, _created = user_service.get_or_create(uid)
        user.refresh_roles()
        if not user.is_player:
            flash("Cette personne n'est pas un·e joueur·euse sur le Discord.", "danger")
            return redirect(url_for(_EDIT_GAME_ENDPOINT, game_id=game_id))
        game_service.register_player(game.slug, user.id, force=True, skip_schedule_check=True)
        flash("Joueur·euse ajouté·e.", "success")
    except NotFoundError:
        flash(_GAME_NOT_FOUND_MESSAGE, "danger")
    except DuplicateRegistrationError:
        flash("Cette personne est déjà inscrite à cette partie.", "danger")
    except ValidationError as e:
        _flash_validation_error(e)
    return redirect(url_for(_EDIT_GAME_ENDPOINT, game_id=game_id))


@admin_bp.route("/games/<int:game_id>/players/<user_id>/remove", methods=["POST"])
@admin_only
def remove_game_player(game_id, user_id):
    """Remove a registered player from a game (admin roster management)."""
    try:
        game = game_service.get_by_id(game_id)
        game_service.unregister_player(game.slug, user_id)
        flash("Joueur·euse retiré·e.", "success")
    except NotFoundError:
        flash(_GAME_NOT_FOUND_MESSAGE, "danger")
    except ValidationError as e:
        _flash_validation_error(e)
    return redirect(url_for(_EDIT_GAME_ENDPOINT, game_id=game_id))


@admin_bp.route("/games/<int:game_id>/viewers/<user_id>/remove", methods=["POST"])
@admin_only
def remove_game_viewer(game_id, user_id):
    """Remove a spectator's follow on a game (admin moderation)."""
    try:
        game = game_service.get_by_id(game_id)
        game_service.unfollow(game.slug, user_id)
        flash("Spectateur·ice retiré·e.", "success")
    except NotFoundError:
        flash(_GAME_NOT_FOUND_MESSAGE, "danger")
    return redirect(url_for(_EDIT_GAME_ENDPOINT, game_id=game_id))


@admin_bp.route("/games/<int:game_id>/award-trophies", methods=["POST"])
@admin_only
def award_game_trophies(game_id):
    """Manually award trophies for an archived game that didn't get them."""
    try:
        game_service.award_trophies(game_id, user_id=session.get("user_id"))
        flash("Badges distribués.", "success")
    except NotFoundError:
        flash(_GAME_NOT_FOUND_MESSAGE, "danger")
    except ValidationError:
        flash("L'annonce doit être archivée avant de distribuer les badges.", "danger")
    except TrophiesAlreadyAwardedError:
        flash("Les badges ont déjà été distribués pour cette annonce.", "danger")
    except TrophyAwardFailedError:
        flash("Certains badges n'ont pas pu être distribués. Veuillez réessayer.", "danger")
    return redirect(url_for(_EDIT_GAME_ENDPOINT, game_id=game_id))


@admin_bp.route("/games/<int:game_id>/revoke-trophies", methods=["POST"])
@admin_only
def revoke_game_trophies(game_id):
    """Manually revoke trophies previously awarded for an archived game."""
    try:
        game_service.revoke_trophies(game_id, user_id=session.get("user_id"))
        flash("Badges retirés.", "success")
    except NotFoundError:
        flash(_GAME_NOT_FOUND_MESSAGE, "danger")
    except ValidationError:
        flash("L'annonce doit être archivée avant de retirer les badges.", "danger")
    except TrophiesNotAwardedError:
        flash("Les badges n'ont pas été distribués pour cette annonce.", "danger")
    return redirect(url_for(_EDIT_GAME_ENDPOINT, game_id=game_id))


@admin_bp.route("/games/<int:game_id>/delete", methods=["POST"])
@admin_only
def delete_game(game_id):
    """Delete a game permanently (database only)."""
    game = game_service.get_by_id(game_id)
    game_service.delete(game.slug)
    flash("Annonce supprimée.", "success")
    return redirect(url_for("admin.list_games"))
