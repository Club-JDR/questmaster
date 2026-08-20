"""Game announcement views."""

import locale
from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from config.constants import (
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
    GamePostingBlockedError,
    NotFoundError,
    PastDateError,
    QuestMasterError,
    ScheduleConflictError,
    SessionConflictError,
    UnauthorizedError,
    ValidationError,
)
from website.services import DiscordService
from website.services.game import GameService
from website.services.game_session import GameSessionService
from website.services.setting import SettingsService
from website.services.special_event import SpecialEventService
from website.services.stats import StatsService
from website.services.system import SystemService
from website.services.user import UserService
from website.services.vtt import VttService
from website.utils.game_filters import get_filtered_games, get_filtered_user_games
from website.utils.game_form_defaults import resolve_game_form_defaults
from website.utils.logger import log_game_event, logger
from website.views.auth import abort_if_not_gm, login_required, who

game_bp = Blueprint("annonces", __name__)

# Configurables
GAME_LIST_TEMPLATE = "games.j2"
GAME_FORM_TEMPLATE = "game_form.j2"
GAME_EDIT_FORM_ROUTE = "annonces.get_game_edit_form"

# Flashed when publishing a draft whose start date is in the past.
_PAST_DATE_MESSAGE = (
    "La date de la partie est dans le passé : la première session serait créée "
    "dans le passé. Modifiez la date ou confirmez la publication."
)

# Flashed when a GM blocked by an admin tries to create or publish a game.
_POSTING_BLOCKED_MESSAGE = (
    "Vous n'êtes pas autorisé·e à poster des annonces. Contactez un·e administrateur·rice."
)

# Datetime format
locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")

# Service instances
game_service = GameService()
session_service = GameSessionService()
discord_service = DiscordService()
special_event_service = SpecialEventService()
system_service = SystemService()
vtt_service = VttService()
stats_service = StatsService()
settings_service = SettingsService()
user_service = UserService()


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def _serialize_games(games):
    """Serialize a list of Game ORM objects to dicts with relationships."""
    return [g.to_dict(include_relationships=True) for g in games]


def _serialize_ref_data():
    """Serialize systems and VTTs for search bar filter dropdowns."""
    return {
        "systems": [s.to_dict() for s in system_service.get_all()],
        "vtts": [v.to_dict() for v in vtt_service.get_all()],
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@game_bp.route("/", methods=["GET"])
def dashboard():
    """Personalised landing dashboard.

    Renders fast: only the open-games preview is computed here. For members, the
    agenda + stats panels (heavier, cached queries) are lazy-loaded client-side
    from :func:`dashboard_panels`. Anonymous visitors see the open games only.
    """
    preview = game_service.get_open_preview(who())
    return render_template(
        "dashboard.j2",
        open_games=_serialize_games(preview["open_games"]),
        open_hidden=preview["open_hidden"],
        agenda=None,
        stats=None,
    )


@game_bp.route("/tableau-de-bord/panneaux/", methods=["GET"])
@login_required
def dashboard_panels():
    """Lazy-loaded fragment: the member's agenda + statistics panels.

    Computes the per-user dashboard data (memoised by ``StatsService`` for a few
    minutes) and renders just the panels markup for client-side injection.
    """
    payload = who()
    data = stats_service.get_dashboard_stats(
        payload["user_id"], settings_service.get_dashboard_agenda_limit()
    )
    return render_template("dashboard_panels.j2", agenda=data["agenda"], stats=data["stats"])


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
        games=_serialize_games(games.items),
        title="Annonces",
        next_url=next_url,
        prev_url=prev_url,
        **_serialize_ref_data(),
    )


@game_bp.route("/annonces/evenement/<int:event_id>/", methods=["GET"])
def search_games_by_event(event_id):
    """Search games filtered by a specific special event."""
    try:
        event = special_event_service.get_by_id(event_id)
    except QuestMasterError:
        flash("L'événement demandé n'existe pas.", "warning")
        return redirect(url_for(SEARCH_GAMES_ROUTE))

    base_query = game_service.repo.query_by_special_event(event_id)

    games, request_args = get_filtered_games(
        request.args,
        who(),
        base_query=base_query,
        default_status=["open"],
        default_type=["oneshot"],
    )

    next_url = (
        url_for(
            "annonces.search_games_by_event",
            event_id=event_id,
            page=games.next_num,
            **request_args,
        )
        if games.has_next
        else None
    )
    prev_url = (
        url_for(
            "annonces.search_games_by_event",
            event_id=event_id,
            page=games.prev_num,
            **request_args,
        )
        if games.has_prev
        else None
    )

    return render_template(
        GAME_LIST_TEMPLATE,
        games=_serialize_games(games.items),
        title=f"Annonces – {event.name}",
        next_url=next_url,
        prev_url=prev_url,
        special_event=event.to_dict(),
        **_serialize_ref_data(),
    )


@game_bp.route("/annonces/cards/", methods=["GET"])
def game_cards():
    """Return game cards HTML fragment for HTMX partial updates."""
    games, _ = get_filtered_games(request.args, who())
    return render_template("game_cards_container.j2", games=_serialize_games(games.items))


@game_bp.route("/annonces/<slug>/", methods=["GET"])
def get_game_details(slug):
    """Display game detail page."""
    payload = who()
    game = game_service.get_by_slug_or_404(slug)
    is_player = "user_id" in payload and game_service.is_player(game, payload["user_id"])
    is_viewer = "user_id" in payload and game_service.is_viewer(game, payload["user_id"])

    game_data = game.to_dict(include_relationships=True)
    game_data["viewers"] = [gv.user.to_dict() for gv in game_service.list_viewers(game.id)]

    return render_template(
        "game_details.j2",
        game=game_data,
        is_player=is_player,
        is_viewer=is_viewer,
        branch_roster=_resolve_branch_roster(payload, game),
    )


def _resolve_branch_roster(payload, game):
    """Build the roster carry-over modal context after branching a one-shot.

    Triggered by a ``?branch_from=<source_slug>`` query param on the new
    one-shot's own details page — set by ``create_branch_game``'s redirect,
    read here rather than threaded through as an extra route so landing on
    this page is otherwise indistinguishable from any other game details
    view. Silently ignored for anyone but the new game's GM/admin, or when
    the source game can no longer be resolved, so a stray/forged query
    param never surfaces someone else's roster.

    Args:
        payload: Auth payload (from ``who()``).
        game: The (new) game whose details page is being rendered.

    Returns:
        Dict with ``source_slug`` and ``players`` (dicts) for the modal, or
        None if the checklist shouldn't be shown.
    """
    source_slug = request.args.get("branch_from")
    if not source_slug:
        return None
    if game.gm_id != payload.get("user_id") and not payload.get("is_admin"):
        return None
    try:
        source_game = game_service.get_by_slug(source_slug)
    except NotFoundError:
        return None
    return {
        "source_slug": source_slug,
        "players": [p.to_dict() for p in source_game.players],
    }


def _resolve_gm_id(payload, data):
    """Resolve the GM a new game should be attributed to.

    The creation form carries a ``gm_id`` field, but it is only ever a
    hidden input pre-filled with the requester's own id — never a real
    picker — so it can't be trusted: a tampered submission could otherwise
    attribute the game to an arbitrary user and dodge that user's own
    ``can_post_games`` block. Regular GMs are therefore always attributed as
    themselves. Admins are trusted to post on behalf of another user, so
    their submitted ``gm_id`` is honored when present.

    Args:
        payload: Auth payload (from ``who()``).
        data: Submitted form data.

    Returns:
        The GM id to attribute the new game to.
    """
    if payload["is_admin"] and data.get("gm_id"):
        return data["gm_id"]
    return payload["user_id"]


def _parse_session_datetime(raw: str) -> datetime:
    """Parse a session date/time value submitted via a ``datetime-local`` input.

    Args:
        raw: Raw form value (e.g. ``"2026-08-20T19:00"``).

    Returns:
        Parsed naive datetime.

    Raises:
        ValueError: If the value is missing or not a valid ISO datetime.
    """
    return datetime.fromisoformat(raw.replace("T", " ")[:16])


@game_bp.route("/annonce/", methods=["GET"])
@login_required
def get_game_form():
    """Get form to create a new game."""
    payload = who()
    abort_if_not_gm(payload)
    if not payload.get("can_post_games", True):
        flash(_POSTING_BLOCKED_MESSAGE, "danger")
        return redirect(url_for(SEARCH_GAMES_ROUTE))
    systems = system_service.get_all()
    vtts = vtt_service.get_all()
    user = user_service.get_by_id(payload["user_id"])
    return render_template(
        GAME_FORM_TEMPLATE,
        systems=systems,
        vtts=vtts,
        defaults=resolve_game_form_defaults(user=user, systems=systems, vtts=vtts),
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
    gm_id = _resolve_gm_id(payload, data)
    action = data.get("action")
    allow_past_date = data.get("confirm_past_date") == "1"

    try:
        game = game_service.create(data, gm_id)
        if action in ("open", "open-silent"):
            try:
                game_service.publish(
                    game.slug,
                    silent=(action == "open-silent"),
                    user_id=payload["user_id"],
                    allow_past_date=allow_past_date,
                )
            except PastDateError:
                # The draft is saved; send the GM back to fix the date or confirm.
                flash(_PAST_DATE_MESSAGE, "warning")
                return redirect(url_for(GAME_EDIT_FORM_ROUTE, slug=game.slug))
            msg = f"Annonce {game.name} postée."
        else:
            msg = f"Annonce {game.name} enregistrée."
    except GamePostingBlockedError:
        flash(_POSTING_BLOCKED_MESSAGE, "danger")
        return redirect(url_for(SEARCH_GAMES_ROUTE))
    except QuestMasterError as e:
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
    allow_past_date = data.get("confirm_past_date") == "1"

    try:
        game = game_service.update(slug, data, user_id=payload["user_id"])
        msg = "Annonce modifiée."

        if was_draft and action in ("open", "open-silent"):
            game_service.publish(
                game.slug,
                silent=(action == "open-silent"),
                user_id=payload["user_id"],
                allow_past_date=allow_past_date,
            )
            msg = (
                "Annonce modifiée et ouverte."
                if action == "open-silent"
                else "Annonce modifiée et postée."
            )
    except PastDateError:
        # Edits are saved (still a draft); send the GM back to fix the date or confirm.
        flash(_PAST_DATE_MESSAGE, "warning")
        return redirect(url_for(GAME_EDIT_FORM_ROUTE, slug=game.slug))
    except GamePostingBlockedError:
        # Edits are saved (still a draft); only the publish step was blocked.
        flash(_POSTING_BLOCKED_MESSAGE, "danger")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))
    except DiscordAPIError as e:
        logger.error(f"Discord error while editing game {slug}: {e}", exc_info=True)
        flash("Une erreur est survenue pendant l'enregistrement.", "danger")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))
    except QuestMasterError as e:
        logger.error(f"Failed to edit game {slug}: {e}", exc_info=True)
        flash("Une erreur est survenue pendant l'enregistrement.", "danger")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))

    flash(msg, "success")
    return redirect(url_for(GAME_DETAILS_ROUTE, slug=game.slug))


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
    game = _get_game_if_participant(payload, slug)

    alert_message = request.form.get("alertMessage")
    try:
        discord_service.send_game_embed(
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


@game_bp.route("/annonces/<slug>/notifier/", methods=["POST"])
@login_required
def notify_players(slug):
    """Notify a game's players by posting a message in its Discord channel."""
    payload = who()
    _get_game_if_authorized(payload, slug)

    message = request.form.get("notifyMessage")
    try:
        game_service.notify_players(slug, message, user_id=payload["user_id"])
        flash("Joueur·euses notifié·es.", "success")
    except ValidationError as e:
        if e.code == "MESSAGE_TOO_LONG":
            overflow = e.details.get("overflow", 0)
            flash(
                f"Le message est trop long de {overflow} caractères une fois les mentions "
                "des joueur·euses ajoutées. Raccourcissez-le et réessayez.",
                "danger",
            )
        else:
            flash("Le message de notification est vide.", "danger")
    except DiscordAPIError as e:
        flash("Une erreur est survenue lors de la notification.", "danger")
        logger.error(f"Failed to notify players for game {slug}: {e}", exc_info=True)

    return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))


@game_bp.route("/annonces/<slug>/sessions/ajouter/", methods=["POST"])
@login_required
def add_game_session(slug):
    """Add session to a game and redirect to the game details."""
    payload = who()
    game = _get_game_if_authorized(payload, slug)

    # Drafts have no Discord channel yet; sessions are created when the game is
    # published. Block adding sessions until then.
    if game.status == "draft":
        flash(
            "Impossible d'ajouter une session à un brouillon. Publiez d'abord l'annonce.",
            "warning",
        )
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))

    try:
        start = _parse_session_datetime(request.values.get("date_start", ""))
        end = _parse_session_datetime(request.values.get("date_end", ""))
    except ValueError:
        flash("Dates de session invalides.", "danger")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))
    start_fmt = start.strftime(HUMAN_TIMEFORMAT)
    end_fmt = end.strftime(HUMAN_TIMEFORMAT)

    try:
        session_service.create(game, start, end)
        log_game_event(
            "create-session",
            game.id,
            f"Une session a été créée du {start_fmt} au {end_fmt}.",
            user_id=payload["user_id"],
        )
        logger.info(f"Session {start}/{end} created for Game {game.id}")
        discord_service.send_game_embed(
            game, embed_type="add-session", start=start_fmt, end=end_fmt
        )
        flash("Session ajoutée.", "success")
    except ValidationError:
        flash(
            "Dates de session invalides : la fin doit suivre le début "
            "et la session ne peut excéder 24 heures.",
            "danger",
        )
    except SessionConflictError as e:
        flash(str(e), "danger")
    except QuestMasterError:
        logger.exception("Failed to create game session")
        flash("Une erreur est survenue pendant la création de la session.", "danger")

    return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))


@game_bp.route("/annonces/<slug>/sessions/<session_id>/editer/", methods=["POST"])
@login_required
def edit_game_session(slug, session_id):
    """Edit game session and redirect to the game details."""
    payload = who()
    game = _get_game_if_authorized(payload, slug)
    session = _get_session_for_game_or_404(game, session_id)

    try:
        new_start = _parse_session_datetime(request.values.get("date_start", ""))
        new_end = _parse_session_datetime(request.values.get("date_end", ""))
    except ValueError:
        flash("Dates de session invalides.", "danger")
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
        discord_service.send_game_embed(
            game,
            embed_type="edit-session",
            start=session.start.strftime(HUMAN_TIMEFORMAT),
            end=session.end.strftime(HUMAN_TIMEFORMAT),
            old_start=old_start,
            old_end=old_end,
        )
        flash("Session modifiée.", "success")
    except ValidationError:
        flash(
            "Dates de session invalides : la fin doit suivre le début "
            "et la session ne peut excéder 24 heures.",
            "danger",
        )
    except SessionConflictError as e:
        flash(str(e), "danger")
    except QuestMasterError:
        logger.exception("Failed to edit game session")
        flash("Erreur lors de la modification de la session.", "danger")

    return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))


@game_bp.route("/annonces/<slug>/sessions/<session_id>/supprimer/", methods=["POST"])
@login_required
def remove_game_session(slug, session_id):
    """Remove session from a game and redirect to the game details."""
    payload = who()
    game = _get_game_if_authorized(payload, slug)
    session = _get_session_for_game_or_404(game, session_id)
    start = session.start.strftime(HUMAN_TIMEFORMAT)
    end = session.end.strftime(HUMAN_TIMEFORMAT)

    try:
        session_service.delete(session)
        log_game_event(
            "delete-session",
            game.id,
            f"Une session a été supprimée du {start} au {end}.",
            user_id=payload["user_id"],
        )
        logger.info(f"Session {start}/{end} of Game {game.slug} has been removed")
        discord_service.send_game_embed(
            game,
            embed_type="del-session",
            start=start,
            end=end,
        )
        flash("Session supprimée.", "success")
    except QuestMasterError:
        logger.exception("Failed to delete game session")
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
    except ScheduleConflictError:
        flash("Vous avez déjà une partie prévue à cette date et heure.", "warning")
    except QuestMasterError:
        logger.exception("Registration failed")
        flash("Une erreur est survenue pendant l'inscription.", "danger")

    return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))


@game_bp.route("/annonces/<slug>/suivre/", methods=["POST"])
@login_required
def toggle_follow_game(slug):
    """Follow/unfollow a game as a viewer (spectator agenda-only signal).

    Purely a personal-agenda toggle: it never notifies the GM nor adds the
    user to the game's roster, role, or channel.
    """
    payload = who()
    user_id = payload["user_id"]
    game = game_service.get_by_slug_or_404(slug)

    try:
        if game_service.is_viewer(game, user_id):
            game_service.unfollow(slug, user_id)
            flash("Vous ne suivez plus cette annonce.", "success")
        else:
            game_service.follow(slug, user_id)
            flash("Vous suivez maintenant cette annonce.", "success")
    except ValidationError:
        flash("Impossible de suivre cette annonce.", "danger")

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
    except QuestMasterError as e:
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
        GAME_FORM_TEMPLATE,
        game=game,
        systems=system_service.get_all(),
        vtts=vtt_service.get_all(),
        clone=True if "cloner" in request.path else False,
        defaults=resolve_game_form_defaults(game=game),
    )


@game_bp.route("/annonces/<slug>/brancher/", methods=["GET"])
@login_required
def get_branch_form(slug):
    """Get the form to branch a campaign into a quick replacement one-shot.

    Unlike "Cloner", this does NOT reuse the campaign's own data (name,
    description, restriction, classification, ambience, img, frequency…):
    the form starts exactly like a brand-new game (the creating user's own
    saved defaults, or the app-wide ones — ``game`` is simply not passed to
    the template), except ``defaults`` is pre-seeded with the structural
    bits worth carrying over — system, VTT (same table, same tools), type
    forced to one-shot, and party_size defaulted to the campaign's current
    headcount (not its own, likely larger, party_size).
    """
    payload = who()
    game = _get_game_if_authorized(payload, slug)
    blocked = _redirect_unless_branchable(game, slug)
    if blocked:
        return blocked

    systems = system_service.get_all()
    vtts = vtt_service.get_all()
    user = user_service.get_by_id(payload["user_id"])
    defaults = resolve_game_form_defaults(user=user, systems=systems, vtts=vtts)
    defaults.update(
        type="oneshot",
        system=game.system_id,
        vtt=game.vtt_id,
        # A one-off replacement table is GM-curated, not open self-registration.
        party_selection=True,
    )
    # Only override the resolved party_size (the user's own saved default, or
    # the app-wide default of 4) when the campaign actually has a headcount
    # to carry over — an empty campaign shouldn't shrink it down to 1.
    headcount = len(game.players)
    if headcount:
        defaults["party_size"] = headcount

    flash("Vous êtes en train de créer un one-shot ponctuel pour cette campagne.", "primary")
    return render_template(
        GAME_FORM_TEMPLATE,
        systems=systems,
        vtts=vtts,
        branch=True,
        branch_source_name=game.name,
        branch_source_slug=slug,
        defaults=defaults,
    )


@game_bp.route("/annonces/<slug>/brancher/", methods=["POST"])
@login_required
def create_branch_game(slug):
    """Create a quick replacement one-shot branched off a campaign.

    Creates the new one-shot as a draft, then immediately publishes it
    silently — resources (channel, role, first session) are created, but the
    game lands ``closed`` to registration and nothing is posted to the
    public announcements channel. This mirrors the plain creation form's
    "Ouvrir (sans publier)" action; the GM opens registration and/or
    publishes for real later, once ready. It matters for the roster step
    next regardless: resources must already exist for carried-over players
    to get real Discord channel access (``register_player`` grants it,
    bypassing the closed status via ``force=True``) rather than just a DB
    record.
    """
    payload = who()
    game = _get_game_if_authorized(payload, slug)
    blocked = _redirect_unless_branchable(game, slug)
    if blocked:
        return blocked

    data = request.values.to_dict()
    gm_id = _resolve_gm_id(payload, data)
    allow_past_date = data.get("confirm_past_date") == "1"

    try:
        new_game = game_service.create(data, gm_id)
    except GamePostingBlockedError:
        flash(_POSTING_BLOCKED_MESSAGE, "danger")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))
    except QuestMasterError as e:
        logger.error(f"Failed to branch game {slug} into a one-shot: {e}", exc_info=True)
        flash("Une erreur est survenue pendant la création du one-shot.", "danger")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))

    try:
        game_service.publish(
            new_game.slug,
            silent=True,
            user_id=payload["user_id"],
            allow_past_date=allow_past_date,
        )
    except PastDateError:
        # The draft is already saved; send the GM back to fix the date or confirm.
        flash(_PAST_DATE_MESSAGE, "warning")
        return redirect(url_for(GAME_EDIT_FORM_ROUTE, slug=new_game.slug))
    except DiscordAPIError as e:
        logger.error(
            f"Failed to set up resources for branched game {new_game.slug}: {e}", exc_info=True
        )
        flash(
            "Le one-shot a été créé en brouillon, mais la mise en place a échoué. "
            "Réessayez de le publier depuis sa page.",
            "warning",
        )
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=new_game.slug))

    flash(f"One-shot « {new_game.name} » créé.", "success")
    return redirect(url_for(GAME_DETAILS_ROUTE, slug=new_game.slug, branch_from=slug))


@game_bp.route("/annonces/<new_slug>/brancher/roster/<source_slug>/", methods=["POST"])
@login_required
def confirm_branch_roster(new_slug, source_slug):
    """Carry over the checked source-game players onto the new one-shot.

    Only players present in the submitted ``known_players`` snapshot are
    considered — mirrors ``_handle_remove_players``'s race-avoidance rule,
    reversed here: a checkbox absent from the submission is treated as
    unchecked (skipped), not as "unknown, ignore".

    Args:
        new_slug: Slug of the freshly created one-shot.
        source_slug: Slug of the source campaign the roster was copied from
            (kept in the URL only to mirror the modal's origin; not otherwise
            used — the checklist itself is entirely driven by the submitted
            checkboxes).
    """
    payload = who()
    _get_game_if_authorized(payload, new_slug)

    data = request.values.to_dict()
    known_ids = {pid for pid in data.get("known_players", "").split(",") if pid}
    kept_ids = [pid for pid in known_ids if pid in data]

    for user_id in kept_ids:
        try:
            game_service.register_player(new_slug, user_id, force=True, skip_schedule_check=True)
        except DuplicateRegistrationError:
            continue
        except QuestMasterError as e:
            logger.warning(f"Failed to carry over player {user_id} to {new_slug}: {e}")

    flash("Liste des joueur·euses reportée sur le one-shot.", "success")
    return redirect(url_for(GAME_DETAILS_ROUTE, slug=new_slug))


@game_bp.route("/mes_annonces/", methods=["GET"])
@login_required
def my_gm_games():
    """List all games where current user is GM."""
    payload = who()
    abort_if_not_gm(payload)
    games, request_args = get_filtered_user_games(
        request.args, payload["user_id"], payload, role="gm"
    )
    return render_template(
        GAME_LIST_TEMPLATE,
        games=_serialize_games(games.items),
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
        **_serialize_ref_data(),
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
        games=_serialize_games(games.items),
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
        **_serialize_ref_data(),
    )


# ---------------------------------------------------------------------------
# Status change helpers (extracted to reduce cognitive complexity)
# ---------------------------------------------------------------------------


def _handle_delete(slug):
    """Delete a game and redirect to home."""
    try:
        game_service.delete(slug)
        flash("Annonce supprimée avec succès.", "success")
    except QuestMasterError:
        logger.exception("Failed to delete game")
        flash("Une erreur est survenue pendant la suppression.", "danger")
    return redirect("/")


def _handle_publish(slug, user_id=None):
    """Publish a draft game and redirect to its detail page."""
    try:
        game_service.publish(slug, user_id=user_id)
        flash("Annonce publiée avec succès.", "success")
    except PastDateError:
        flash(_PAST_DATE_MESSAGE, "warning")
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
    except QuestMasterError:
        logger.exception("Failed to change game status")
        flash("Une erreur est survenue pendant la modification de statut.", "danger")

    return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))


# ---------------------------------------------------------------------------
# Registration helpers
# ---------------------------------------------------------------------------


def _handle_remove_players(game, data):
    """Remove players that were shown in the modal but came back unchecked.

    Only players present in the submitted ``known_players`` snapshot are eligible
    for removal, so anyone who registered after the modal was opened is never
    touched (avoids a race with concurrent registrations).

    Args:
        game: Game whose players are being managed.
        data: Submitted form data (checkbox names + ``known_players`` snapshot).
    """
    known_ids = {pid for pid in data.get("known_players", "").split(",") if pid}
    players_to_remove = [
        p for p in game.players if str(p.id) in known_ids and str(p.id) not in data
    ]
    for player in players_to_remove:
        game_service.unregister_player(game.slug, player.id)


def _handle_add_player(game, slug, data, payload):
    """Add a new player to the game by Discord ID via service."""
    uid = data.get("discord_id")
    if not uid:
        flash("Identifiant Discord manquant.", "danger")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))

    user, created = user_service.get_or_create(str(uid))
    if created:
        logger.info(f"User {uid} created in database")

    user.refresh_roles()
    if not user.is_player:
        flash("Cette personne n'est pas un·e joueur·euse sur le Discord", "danger")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))

    force = payload["user_id"] == game.gm_id or payload.get("is_admin", False)
    game_service.register_player(slug, user.id, force=force, skip_schedule_check=force)


# ---------------------------------------------------------------------------
# Authorization helpers
# ---------------------------------------------------------------------------


def _get_game_if_authorized(payload, slug):
    """Return game if user is the game's GM or an admin, else raise.

    Args:
        payload: Auth payload (from ``who()``).
        slug: Slug of the game to load.

    Returns:
        The authorized Game instance.

    Raises:
        UnauthorizedError: If the caller is neither the game's GM nor an admin.
    """
    game = game_service.get_by_slug_or_404(slug)
    if game.gm_id != payload["user_id"] and not payload["is_admin"]:
        raise UnauthorizedError(
            "Only the game's GM or an admin may perform this operation.",
            action="game_authorized",
        )
    return game


def _get_session_for_game_or_404(game, session_id):
    """Return the session if it belongs to ``game``, else 404.

    Being authorized on ``game`` (GM/admin) only grants control over that
    game's own sessions — without this check, a foreign ``session_id`` in
    the URL would let a GM edit or delete another game's session (IDOR).
    404, not 403: from the caller's perspective a foreign session simply
    doesn't exist under this game.

    Args:
        game: The (already-authorized) game the session must belong to.
        session_id: Session ID from the route.

    Returns:
        The GameSession instance.
    """
    session = session_service.get_by_id_or_404(session_id)
    if session.game_id != game.id:
        abort(404)
    return session


def _redirect_unless_branchable(game, slug):
    """Redirect to the game details page unless the game may be branched.

    Branching into a quick one-shot only makes sense for a published
    campaign: a draft has no roster or Discord resources to branch off yet,
    and an archived campaign is already wrapped up. Branching a one-shot into
    another one-shot is also just "Cloner" with extra steps, hence the type
    restriction too.

    Args:
        game: Candidate source game.
        slug: Its slug (used as the redirect target on failure).

    Returns:
        A redirect Response if branching isn't allowed right now, else None.
    """
    if game.type != "campaign" or game.status in ("draft", "archived"):
        flash("Seule une campagne publiée peut être branchée en one-shot.", "danger")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))
    return None


def _get_game_if_participant(payload, slug):
    """Return game if user is GM, admin, or a registered player, else raise.

    Unlike ``_get_game_if_authorized`` (GM/admin only), this also grants
    access to players registered for the game.

    Args:
        payload: Auth payload (from ``who()``).
        slug: Slug of the game to load.

    Returns:
        The authorized Game instance.

    Raises:
        UnauthorizedError: If the caller is neither the game's GM/an admin
            nor a registered player.
    """
    game = game_service.get_by_slug_or_404(slug)
    if (
        game.gm_id != payload["user_id"]
        and not payload["is_admin"]
        and not game_service.is_player(game, payload["user_id"])
    ):
        raise UnauthorizedError(
            "Only the game's GM, an admin, or a registered player may perform this operation.",
            action="game_participant",
        )
    return game
