"""Game announcement views."""

from datetime import datetime, timezone
import locale

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy import case
from sqlalchemy.sql import func, or_, and_

from config.constants import (
    DEFAULT_TIMEFORMAT,
    GAME_DETAILS_ROUTE,
    GAME_STATUS_LABELS,
    GAMES_PER_PAGE,
    HUMAN_TIMEFORMAT,
    SEARCH_GAMES_ROUTE,
)
from website.bot import get_bot
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
from website.services.game import GameService
from website.services.game_session import GameSessionService
from website.services.special_event import SpecialEventService
from website.services.user import UserService
from website.utils.game_embeds import send_discord_embed
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
    games, request_args = _get_filtered_games(request.args)

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
    special_event_service = SpecialEventService()
    try:
        event = special_event_service.get_by_id(event_id)
    except QuestMasterError:
        flash("L'événement demandé n'existe pas.", "warning")
        return redirect(url_for(SEARCH_GAMES_ROUTE))

    base_query = Game.query.filter(Game.special_event_id == event_id)

    games, request_args = _get_filtered_games(
        request.args,
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
    games, _ = _get_filtered_games(request.args)
    return render_template("game_cards_container.j2", games=games.items)


@game_bp.route("/annonces/<slug>/", methods=["GET"])
def get_game_details(slug):
    """Display game detail page."""
    payload = who()
    game = game_service.get_by_slug_or_404(slug)
    is_player = "user_id" in payload and any(
        p.id == payload["user_id"] for p in game.players
    )
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
    bot = get_bot()

    try:
        game = game_service.create(data, gm_id)
        if action in ("open", "open-silent"):
            game_service.publish(game.slug, bot, silent=(action == "open-silent"))
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
    bot = get_bot()

    try:
        game = game_service.update(slug, data, bot)
        msg = "Annonce modifiée."

        if was_draft and action in ("open", "open-silent"):
            game_service.publish(slug, bot, silent=(action == "open-silent"))
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
    bot = get_bot()
    status = request.values.get("status")
    award_trophies = "award_trophies" in request.form

    if status == "deleted":
        return _handle_delete(slug)

    if status == "publish":
        return _handle_publish(slug, bot)

    return _handle_status_transition(slug, game, bot, status, award_trophies)


@game_bp.route("/annonces/<slug>/alert/", methods=["POST"])
@login_required
def send_alert(slug):
    """Send an alert message to the Discord channel and register a game event."""
    payload = who()
    game = game_service.get_by_slug_or_404(slug)

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
        send_discord_embed(
            game, type="alert", alert_message=alert_message, player=payload["user_id"]
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
        )
        logger.info(f"Session {start}/{end} created for Game {game.id}")
        send_discord_embed(game, type="add-session", start=start, end=end)
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
            f"Une session a été éditée : {old_start} → {old_end}, remplacée par {new_start} → {new_end}.",
        )
        logger.info(
            f"Session {old_start}/{old_end} of Game {game.slug} updated to {new_start}/{new_end}"
        )
        send_discord_embed(
            game,
            type="edit-session",
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
    session = session_service.get_by_id_or_404(session_id)
    start = session.start
    end = session.end

    try:
        session_service.delete(session)
        log_game_event(
            "delete-session",
            game.id,
            f"Une session a été supprimée de {start} à {end}.",
        )
        logger.info(f"Session {start}/{end} of Game {game.slug} has been removed")
        send_discord_embed(
            game,
            type="del-session",
            start=start.strftime(HUMAN_TIMEFORMAT),
            end=end.strftime(HUMAN_TIMEFORMAT),
        )
    except Exception:
        flash("Erreur lors de la suppression de la session.", "danger")
    flash("Session supprimée.", "success")
    return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))


@game_bp.route("/annonces/<slug>/inscription/", methods=["POST"])
@login_required
def register_game(slug):
    """Register a player to a game."""
    payload = who()
    user_id = payload["user_id"]
    bot = get_bot()
    game = game_service.get_by_slug_or_404(slug)

    if game.gm_id == user_id:
        flash("Vous ne pouvez pas vous inscrire à votre propre partie.", "warning")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))

    try:
        game_service.register_player(slug, user_id, bot, force=game.party_selection)
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
    bot = get_bot()
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
            _handle_remove_players(game, data, bot)
        elif action == "add":
            _handle_add_player(game, slug, data, payload, bot)
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
    games, request_args = _get_filtered_user_games(
        request.args, payload["user_id"], role="gm"
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
    games, request_args = _get_filtered_user_games(
        request.args, payload["user_id"], role="player"
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


def _handle_publish(slug, bot):
    """Publish a draft game and redirect to its detail page."""
    try:
        game_service.publish(slug, bot)
        flash("Annonce publiée avec succès.", "success")
    except ValidationError as e:
        flash(e.message, "danger")
    except DiscordAPIError as e:
        logger.error(f"Failed to publish game {slug}: {e}")
        flash("Une erreur est survenue pendant la publication.", "danger")
    return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))


def _handle_status_transition(slug, game, bot, status, award_trophies):
    """Apply a status transition (close/reopen/archive) and redirect."""
    if status not in GAME_STATUS_LABELS:
        flash("Statut demandé non géré.", "danger")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))

    try:
        if status == "closed":
            game_service.close(slug, bot)
        elif status == "open":
            game_service.reopen(slug, bot)
        else:
            game_service.archive(slug, bot, award_trophies=award_trophies)
        flash(f"Annonce {game.name} {GAME_STATUS_LABELS[status]}.", "success")
    except Exception:
        flash("Une erreur est survenue pendant la modification de statut.", "danger")

    return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))


# ---------------------------------------------------------------------------
# Registration helpers
# ---------------------------------------------------------------------------


def _handle_remove_players(game, data, bot):
    """Remove unchecked players from the game via service."""
    players_to_remove = [p for p in game.players if str(p.id) not in data]
    for player in players_to_remove:
        game_service.unregister_player(game.slug, player.id, bot)


def _handle_add_player(game, slug, data, payload, bot):
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
    game_service.register_player(slug, user.id, bot, force=force)


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


# ---------------------------------------------------------------------------
# Search / filter helpers
# ---------------------------------------------------------------------------


def _parse_multi_checkbox_filter(source, keys):
    filters = []
    args = {}
    for key in keys:
        if source.get(key, type=bool):
            filters.append(key)
            args[key] = "on"
    return filters, args


def _build_base_filters(request_args, name, system, vtt):
    filters = []
    if name:
        request_args["name"] = name
        filters.append(Game.name.ilike(f"%{name}%"))
    if system:
        request_args["system"] = system
        filters.append(Game.system_id == system)
    if vtt:
        request_args["vtt"] = vtt
        filters.append(Game.vtt_id == vtt)
    return filters


def _build_status_filters(statuses, user_payload):
    filters = []
    for s in statuses:
        if s != "draft":
            filters.append(Game.status == s)
        elif user_payload.get("is_admin"):
            filters.append(Game.status == "draft")
        else:
            filters.append(
                and_(Game.status == "draft", Game.gm_id == user_payload.get("user_id"))
            )
    return or_(*filters)


def _normalize_search_defaults(
    status, game_type, restriction,
    default_status=None, default_type=None, default_restriction=None,
):
    if not status:
        status = default_status or ["open"]
    if not game_type:
        game_type = default_type or ["oneshot", "campaign"]
    if not restriction:
        restriction = default_restriction or ["all", "16+", "18+"]
    return status, game_type, restriction


def _get_filtered_games(
    request_args_source,
    base_query=None,
    default_status=None,
    default_type=None,
    default_restriction=None,
):
    request_args = {}
    now = datetime.now(timezone.utc)
    user_payload = who()

    status, status_args = _parse_multi_checkbox_filter(
        request_args_source, ["open", "closed", "archived", "draft"]
    )
    game_type, type_args = _parse_multi_checkbox_filter(
        request_args_source, ["oneshot", "campaign"]
    )
    restriction, restriction_args = _parse_multi_checkbox_filter(
        request_args_source, ["all", "16+", "18+"]
    )
    request_args.update(status_args)
    request_args.update(type_args)
    request_args.update(restriction_args)

    status, game_type, restriction = _normalize_search_defaults(
        status, game_type, restriction,
        default_status=default_status,
        default_type=default_type,
        default_restriction=default_restriction,
    )

    name = request_args_source.get("name", type=str)
    system = request_args_source.get("system", type=int)
    vtt = request_args_source.get("vtt", type=int)

    queries = [
        Game.restriction.in_(restriction),
        Game.type.in_(game_type),
    ]
    queries += _build_base_filters(request_args, name, system, vtt)
    queries.append(_build_status_filters(status, user_payload))

    status_order = case(
        (Game.status == "draft", 0),
        (Game.status == "open", 1),
        (Game.status == "closed", 2),
        (Game.status == "archived", 3),
    )
    is_future = case((Game.date >= now, 0), else_=1)
    time_distance = func.abs(func.extract("epoch", Game.date - now))

    page = request_args_source.get("page", 1, type=int)
    query = base_query or Game.query
    games = (
        query.filter(*queries)
        .order_by(status_order, is_future, time_distance)
        .paginate(page=page, per_page=GAMES_PER_PAGE, error_out=False)
    )

    return games, request_args


def _get_filtered_user_games(request_args_source, user_id, role="gm"):
    user = UserService().repo.get_by_id(user_id)
    if not user:
        return [], {}

    if role == "gm":
        base_query = Game.query.filter(Game.gm_id == user_id)
    elif role == "player":
        game_ids = [game.id for game in user.games]
        base_query = Game.query.filter(Game.id.in_(game_ids))
    else:
        raise ValidationError("Invalid role.", field="role")

    return _get_filtered_games(
        request_args_source,
        base_query,
        default_status=["draft", "open", "closed", "archived"],
    )
