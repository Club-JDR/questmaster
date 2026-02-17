"""Game announcement views."""

import locale
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from config.constants import (
    DEFAULT_TIMEFORMAT,
    GAME_DETAILS_ROUTE,
    GAME_STATUS_LABELS,
    HUMAN_TIMEFORMAT,
    SEARCH_GAMES_ROUTE,
)
from website.exceptions import (
    DiscordAPIError,
    DuplicateRegistrationError,
    GameClosedError,
    GameFullError,
    QuestMasterError,
    SessionConflictError,
    UnauthorizedError,
    ValidationError,
)
from website.models import Game, System, Vtt
from website.services import DiscordService
from website.services.game import GameService
from website.services.game_session import GameSessionService
from website.services.special_event import SpecialEventService
from website.services.user import UserService
from website.utils.game_filters import get_filtered_games, get_filtered_user_games
from website.utils.logger import log_game_event, logger
from website.views.auth import login_required, who

game_bp = Blueprint("annonces", __name__)

# Configurables
GAME_LIST_TEMPLATE = "games.j2"

# Datetime format
locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")

# Service instances
game_service = GameService()
session_service = GameSessionService()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@game_bp.route("/", methods=["GET"])
@game_bp.route("/annonces/", methods=["GET"])
def search_games():
    """Search and list game announcements with filtering and pagination."""
    games, request_args = get_filtered_games(request.args, who())

    next_url = (
        url_for(SEARCH_GAMES_ROUTE, page=games.next_num, **request_args)
        if games.has_next
        else None
    )
    prev_url = (
        url_for(SEARCH_GAMES_ROUTE, page=games.prev_num, **request_args)
        if games.has_prev
        else None
    )

    return render_template(
        GAME_LIST_TEMPLATE,
        games=games.items,
        title="Annonces",
        next_url=next_url,
        prev_url=prev_url,
        systems=System.get_systems(),
        vtts=Vtt.get_vtts(),
    )


@game_bp.route("/annonces/evenement/<int:event_id>/", methods=["GET"])
def search_games_by_event(event_id):
    """Search games filtered by a specific special event."""
    special_event_service = SpecialEventService()
    try:
        event = special_event_service.get_by_id(event_id)
    except QuestMasterError:
        flash("L'événement demandé n'existe pas.", "warning")
        return redirect(url_for(SEARCH_GAMES_ROUTE))

    base_query = Game.query.filter(Game.special_event_id == event_id)

    games, request_args = get_filtered_games(
        request.args,
        who(),
        base_query=base_query,
        default_status=["open"],
        default_type=["oneshot"],
    )

    next_url = (
        url_for(
            "game.search_games_by_event",
            event_id=event_id,
            page=games.next_num,
            **request_args,
        )
        if games.has_next
        else None
    )
    prev_url = (
        url_for(
            "game.search_games_by_event",
            event_id=event_id,
            page=games.prev_num,
            **request_args,
        )
        if games.has_prev
        else None
    )

    return render_template(
        GAME_LIST_TEMPLATE,
        games=games.items,
        title=f"Annonces – {event.name}",
        next_url=next_url,
        prev_url=prev_url,
        systems=System.get_systems(),
        vtts=Vtt.get_vtts(),
        special_event=event,
    )


@game_bp.route("/annonces/cards/")
def game_cards():
    """Return game cards HTML fragment for HTMX partial updates."""
    games, _ = get_filtered_games(request.args, who())
    return render_template("game_cards_container.j2", games=games.items)


@game_bp.route("/annonces/<slug>/", methods=["GET"])
def get_game_details(slug):
    """Display game detail page."""
    payload = who()
    game = game_service.get_by_slug_or_404(slug)
    is_player = "user_id" in payload and any(p.id == payload["user_id"] for p in game.players)
    return render_template("game_details.j2", game=game, is_player=is_player)


@game_bp.route("/annonce/", methods=["GET"])
@login_required
def get_game_form():
    """Get form to create a new game."""
    payload = who()
    _abort_if_not_gm(payload)
    return render_template(
        "game_form.j2",
        systems=System.get_systems(),
        vtts=Vtt.get_vtts(),
    )


@game_bp.route("/annonce/", methods=["POST"])
@login_required
def create_game():
    """Create a new game announcement."""
    payload = who()
    if not payload["is_gm"] and not payload["is_admin"]:
        logger.warning(
            f"Unauthorized game creation attempt by user: {payload.get('user_id', 'Unknown')}"
        )
        flash("Vous devez être MJ pour poster une annonce.", "danger")
        return redirect(url_for(SEARCH_GAMES_ROUTE))

    data = request.values.to_dict()
    gm_id = data["gm_id"]
    action = data["action"]

    try:
        game = game_service.create(data, gm_id)
        if action in ("open", "open-silent"):
            game_service.publish(
                game.slug, silent=(action == "open-silent"), user_id=payload["user_id"]
            )
            msg = f"Annonce {game.name} postée."
        else:
            msg = f"Annonce {game.name} enregistrée."
    except Exception as e:
        logger.error(f"Failed to save game: {e}", exc_info=True)
        flash("Une erreur est survenue pendant la création de l'annonce.", "danger")
        return redirect(url_for(SEARCH_GAMES_ROUTE))

    flash(msg, "success")
    return redirect(url_for(GAME_DETAILS_ROUTE, slug=game.slug))


@game_bp.route("/annonces/<slug>/editer/", methods=["POST"])
@login_required
def edit_game(slug):
    """Edit an existing game announcement."""
    payload = who()
    game = _get_game_if_authorized(payload, slug)
    was_draft = game.status == "draft"
    data = request.values.to_dict()
    action = data.get("action")

    try:
        game = game_service.update(slug, data, user_id=payload["user_id"])
        msg = "Annonce modifiée."

        if was_draft and action in ("open", "open-silent"):
            game_service.publish(
                slug, silent=(action == "open-silent"), user_id=payload["user_id"]
            )
            msg = (
                "Annonce modifiée et ouverte."
                if action == "open-silent"
                else "Annonce modifiée et postée."
            )
    except DiscordAPIError as e:
        logger.error(f"Discord error while editing game {slug}: {e}", exc_info=True)
        flash("Une erreur est survenue pendant l'enregistrement.", "danger")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))
    except Exception as e:
        logger.error(f"Failed to edit game {slug}: {e}", exc_info=True)
        flash("Une erreur est survenue pendant l'enregistrement.", "danger")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))

    flash(msg, "success")
    return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))


@game_bp.route("/annonces/<slug>/statut/", methods=["POST"])
@login_required
def change_game_status(slug):
    """Change game status and redirect to the game details."""
    payload = who()
    game = _get_game_if_authorized(payload, slug)
    status = request.values.get("status")
    award_trophies = "award_trophies" in request.form

    if status == "deleted":
        return _handle_delete(slug)

    if status == "publish":
        return _handle_publish(slug, user_id=payload["user_id"])

    return _handle_status_transition(
        slug, game, status, award_trophies, user_id=payload["user_id"]
    )


@game_bp.route("/annonces/<slug>/alert/", methods=["POST"])
@login_required
def send_alert(slug):
    """Send an alert message to the Discord channel and register a game event."""
    payload = who()
    game = game_service.get_by_slug_or_404(slug)
    discord = DiscordService()

    if (
        game.gm_id != payload["user_id"]
        and not payload["is_admin"]
        and not any(player.id == payload["user_id"] for player in game.players)
    ):
        flash(
            "Vous n'êtes pas autorisé·e à envoyer une alerte pour cette partie.",
            "danger",
        )
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))

    alert_message = request.form.get("alertMessage")
    try:
        discord.send_game_embed(
            game,
            embed_type="alert",
            alert_message=alert_message,
            player=payload["user_id"],
        )
        flash("Signalement effectué.", "success")
        log_game_event("alert", game.id, "Un signalement a été fait.")
    except DiscordAPIError as e:
        flash("Une erreur est survenue lors du signalement.", "danger")
        logger.error(f"Failed to send alert: {e}", exc_info=True)

    return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))


@game_bp.route("/annonces/<slug>/sessions/ajouter/", methods=["POST"])
@login_required
def add_game_session(slug):
    """Add session to a game and redirect to the game details."""
    payload = who()
    game = _get_game_if_authorized(payload, slug)
    discord = DiscordService()
    start = datetime.strptime(request.values.get("date_start"), DEFAULT_TIMEFORMAT)
    end = datetime.strptime(request.values.get("date_end"), DEFAULT_TIMEFORMAT)

    if start >= end:
        flash(
            "Impossible d'ajouter une session qui se termine avant de commencer.",
            "danger",
        )
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))

    try:
        session_service.create(game, start, end)
        log_game_event(
            "create-session",
            game.id,
            f"Une session a été créée de {start} à {end}.",
            user_id=payload["user_id"],
        )
        logger.info(f"Session {start}/{end} created for Game {game.id}")
        discord.send_game_embed(game, embed_type="add-session", start=start, end=end)
        flash("Session ajoutée.", "success")
    except (ValidationError, SessionConflictError) as e:
        flash(str(e), "danger")
    except Exception:
        flash("Une erreur est survenue pendant la création de la session.", "danger")

    return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))


@game_bp.route("/annonces/<slug>/sessions/<session_id>/editer/", methods=["POST"])
@login_required
def edit_game_session(slug, session_id):
    """Edit game session and redirect to the game details."""
    payload = who()
    game = _get_game_if_authorized(payload, slug)
    discord = DiscordService()
    session = session_service.get_by_id_or_404(session_id)

    new_start = datetime.strptime(request.values.get("date_start"), DEFAULT_TIMEFORMAT)
    new_end = datetime.strptime(request.values.get("date_end"), DEFAULT_TIMEFORMAT)

    if new_start >= new_end:
        flash(
            "Impossible d'ajouter une session qui se termine avant de commencer.",
            "danger",
        )
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))

    old_start = session.start.strftime(HUMAN_TIMEFORMAT)
    old_end = session.end.strftime(HUMAN_TIMEFORMAT)

    try:
        session_service.update(session, new_start, new_end)
        log_game_event(
            "edit-session",
            game.id,
            f"Une session a été éditée : {old_start} → {old_end}, "
            f"remplacée par {new_start} → {new_end}.",
            user_id=payload["user_id"],
        )
        logger.info(
            f"Session {old_start}/{old_end} of Game {game.slug} updated to {new_start}/{new_end}"
        )
        discord.send_game_embed(
            game,
            embed_type="edit-session",
            start=session.start.strftime(HUMAN_TIMEFORMAT),
            end=session.end.strftime(HUMAN_TIMEFORMAT),
            old_start=old_start,
            old_end=old_end,
        )
        flash("Session modifiée.", "success")
    except (ValidationError, SessionConflictError) as e:
        flash(str(e), "danger")
    except Exception:
        flash("Erreur lors de la modification de la session.", "danger")

    return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))


@game_bp.route("/annonces/<slug>/sessions/<session_id>/supprimer/", methods=["POST"])
@login_required
def remove_game_session(slug, session_id):
    """Remove session from a game and redirect to the game details."""
    payload = who()
    game = _get_game_if_authorized(payload, slug)
    discord = DiscordService()
    session = session_service.get_by_id_or_404(session_id)
    start = session.start
    end = session.end

    try:
        session_service.delete(session)
        log_game_event(
            "delete-session",
            game.id,
            f"Une session a été supprimée de {start} à {end}.",
            user_id=payload["user_id"],
        )
        logger.info(f"Session {start}/{end} of Game {game.slug} has been removed")
        discord.send_game_embed(
            game,
            embed_type="del-session",
            start=start.strftime(HUMAN_TIMEFORMAT),
            end=end.strftime(HUMAN_TIMEFORMAT),
        )
        flash("Session supprimée.", "success")
    except Exception:
        flash("Erreur lors de la suppression de la session.", "danger")
    return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))


@game_bp.route("/annonces/<slug>/inscription/", methods=["POST"])
@login_required
def register_game(slug):
    """Register a player to a game."""
    payload = who()
    user_id = payload["user_id"]
    game = game_service.get_by_slug_or_404(slug)

    if game.gm_id == user_id:
        flash("Vous ne pouvez pas vous inscrire à votre propre partie.", "warning")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))

    try:
        game_service.register_player(slug, user_id, force=game.party_selection)
        flash("Vous êtes inscrit·e.", "success")
    except DuplicateRegistrationError:
        flash("Vous êtes déjà inscrit·e à cette partie.", "warning")
    except GameFullError:
        flash("La partie est complète.", "danger")
    except GameClosedError:
        flash("La partie est fermée aux inscriptions.", "warning")
    except Exception:
        logger.exception("Registration failed")
        flash("Une erreur est survenue pendant l'inscription.", "danger")

    return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))


@game_bp.route("/annonces/<slug>/gerer/", methods=["POST"])
@login_required
def manage_game_registration(slug):
    """Manage player registration for a game."""
    payload = who()
    user_id = payload["user_id"]
    game = game_service.get_by_slug_or_404(slug)

    if game.status == "archived":
        flash("Impossible de gérer les joueur·euses d'une partie archivée.", "danger")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))
    if game.gm_id != user_id and not payload["is_admin"]:
        flash("Vous n'êtes pas autorisé·e à faire cette action.", "danger")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))

    data = request.values.to_dict()
    action = data.get("action")

    try:
        if action == "manage":
            _handle_remove_players(game, data)
        elif action == "add":
            _handle_add_player(game, slug, data, payload)
        else:
            flash("Action demandée non gérée.", "danger")
            return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))
    except Exception as e:
        logger.exception("Error during game registration management")
        flash(f"Erreur pendant l'inscription: {e}.", "danger")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))

    flash("Liste des joueur·euses mise à jour.", "success")
    return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))


@game_bp.route("/annonces/<slug>/cloner/", methods=["GET"])
@game_bp.route("/annonces/<slug>/editer/", methods=["GET"])
@login_required
def get_game_edit_form(slug):
    """Get form to edit or clone a game."""
    payload = who()
    game = _get_game_if_authorized(payload, slug)
    if request.path.endswith("/cloner/"):
        flash("Vous êtes en train de cloner une annonce.", "primary")
    else:
        flash("Vous êtes en train de modifier une annonce.", "primary")
    return render_template(
        "game_form.j2",
        game=game,
        systems=System.get_systems(),
        vtts=Vtt.get_vtts(),
        clone=True if "cloner" in request.path else False,
    )


@game_bp.route("/mes_annonces/", methods=["GET"])
@login_required
def my_gm_games():
    """List all games where current user is GM."""
    payload = who()
    _abort_if_not_gm(payload)
    games, request_args = get_filtered_user_games(
        request.args, payload["user_id"], payload, role="gm"
    )
    return render_template(
        GAME_LIST_TEMPLATE,
        games=games.items,
        gm_only=True,
        title="Mes annonces",
        next_url=(
            url_for("annonces.my_gm_games", page=games.next_num, **request_args)
            if games.has_next
            else None
        ),
        prev_url=(
            url_for("annonces.my_gm_games", page=games.prev_num, **request_args)
            if games.has_prev
            else None
        ),
        systems=System.get_systems(),
        vtts=Vtt.get_vtts(),
    )


@game_bp.route("/mes_parties/", methods=["GET"])
@login_required
def my_games():
    """List all current user non-archived games as player."""
    payload = who()
    games, request_args = get_filtered_user_games(
        request.args, payload["user_id"], payload, role="player"
    )
    return render_template(
        GAME_LIST_TEMPLATE,
        games=games.items,
        title="Mes parties en cours",
        next_url=(
            url_for("annonces.my_games", page=games.next_num, **request_args)
            if games.has_next
            else None
        ),
        prev_url=(
            url_for("annonces.my_games", page=games.prev_num, **request_args)
            if games.has_prev
            else None
        ),
        systems=System.get_systems(),
        vtts=Vtt.get_vtts(),
    )


# ---------------------------------------------------------------------------
# Status change helpers (extracted to reduce cognitive complexity)
# ---------------------------------------------------------------------------


def _handle_delete(slug):
    """Delete a game and redirect to home."""
    try:
        game_service.delete(slug)
        flash("Annonce supprimée avec succès.", "success")
    except Exception as e:
        flash("Une erreur est survenue pendant la suppression.", "danger")
        logger.error(e)
    return redirect("/")


def _handle_publish(slug, user_id=None):
    """Publish a draft game and redirect to its detail page."""
    try:
        game_service.publish(slug, user_id=user_id)
        flash("Annonce publiée avec succès.", "success")
    except ValidationError as e:
        flash(e.message, "danger")
    except DiscordAPIError as e:
        logger.error(f"Failed to publish game {slug}: {e}")
        flash("Une erreur est survenue pendant la publication.", "danger")
    return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))


def _handle_status_transition(slug, game, status, award_trophies, user_id=None):
    """Apply a status transition (close/reopen/archive) and redirect."""
    if status not in GAME_STATUS_LABELS:
        flash("Statut demandé non géré.", "danger")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))

    try:
        if status == "closed":
            game_service.close(slug, user_id=user_id)
        elif status == "open":
            game_service.reopen(slug, user_id=user_id)
        else:
            game_service.archive(slug, award_trophies=award_trophies, user_id=user_id)
        flash(f"Annonce {game.name} {GAME_STATUS_LABELS[status]}.", "success")
    except Exception:
        flash("Une erreur est survenue pendant la modification de statut.", "danger")

    return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))


# ---------------------------------------------------------------------------
# Registration helpers
# ---------------------------------------------------------------------------


def _handle_remove_players(game, data):
    """Remove unchecked players from the game via service."""
    players_to_remove = [p for p in game.players if str(p.id) not in data]
    for player in players_to_remove:
        game_service.unregister_player(game.slug, player.id)


def _handle_add_player(game, slug, data, payload):
    """Add a new player to the game by Discord ID via service."""
    uid = data.get("discord_id")
    if not uid:
        flash("Identifiant Discord manquant.", "danger")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))

    user, created = UserService().get_or_create(str(uid))
    if created:
        logger.info(f"User {uid} created in database")

    user.refresh_roles()
    if not user.is_player:
        flash("Cette personne n'est pas un·e joueur·euse sur le Discord", "danger")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))

    force = payload["user_id"] == game.gm_id or payload.get("is_admin", False)
    game_service.register_player(slug, user.id, force=force)


# ---------------------------------------------------------------------------
# Authorization helpers
# ---------------------------------------------------------------------------


def _abort_if_not_gm(payload):
    """Raise UnauthorizedError if user is not GM."""
    if not payload["is_gm"]:
        raise UnauthorizedError("GM access required.", action="gm")


def _get_game_if_authorized(payload, slug):
    """Return game if user is the game's GM or an admin, else redirect."""
    game = game_service.get_by_slug_or_404(slug)
    if game.gm_id != payload["user_id"] and not payload["is_admin"]:
        flash("Seul·e le·a MJ de l'annonce peut faire cette opération.", "danger")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))
    return game
