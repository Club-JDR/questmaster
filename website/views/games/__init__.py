from flask import (
    request,
    render_template,
    redirect,
    url_for,
    abort,
    Blueprint,
    g,
    flash,
)
from website.extensions import db
from website.bot import get_bot
from website.models import Game, User, System, Vtt, GameSession
from website.views.auth import who, login_required
from website.utils.logger import logger
from .embeds import send_discord_embed, DEFAULT_TIMEFORMAT, HUMAN_TIMEFORMAT
from .helpers import *
from datetime import datetime
import locale


game_bp = Blueprint("annonces", __name__)

# Configurables
GAME_LIST_TEMPLATE = "games.j2"

# Datetime format
locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")


@game_bp.route("/", methods=["GET"])
@game_bp.route("/annonces/", methods=["GET"])
def search_games():
    games, request_args = get_filtered_games(request.args)

    next_url = (
        url_for("annonces.search_games", page=games.next_num, **request_args)
        if games.has_next
        else None
    )
    prev_url = (
        url_for("annonces.search_games", page=games.prev_num, **request_args)
        if games.has_prev
        else None
    )

    return render_template(
        GAME_LIST_TEMPLATE,
        payload=who(),
        games=games.items,
        title="Annonces",
        next_url=next_url,
        prev_url=prev_url,
        systems=System.get_systems(),
        vtts=Vtt.get_vtts(),
    )


@game_bp.route("/annonces/cards/")
def game_cards():
    games, _ = get_filtered_games(request.args)
    return render_template("game_cards_container.j2", games=games.items)


@game_bp.route("/annonces/<game_id>/", methods=["GET"])
def get_game_details(game_id):
    """
    Get details for a given game.
    """
    payload = who()
    game = db.get_or_404(Game, game_id)
    is_player = False
    for player in game.players:
        if payload != {} and payload["user_id"] == player.id:
            is_player = True
    return render_template(
        "game_details.j2", payload=payload, game=game, is_player=is_player
    )


@game_bp.route("/annonce/", methods=["GET"])
@login_required
def get_game_form():
    """
    Get form to create a new game.
    """
    payload = who()
    abort_if_not_gm(payload)
    return render_template(
        "game_form.j2",
        payload=payload,
        systems=System.get_systems(),
        vtts=Vtt.get_vtts(),
    )


@game_bp.route("/annonce/", methods=["POST"])
@login_required
def create_game():
    payload = who()
    bot = get_bot()

    if not payload["is_gm"] and not payload["is_admin"]:
        logger.warning(
            f"Unauthorized game creation attempt by user: {payload.get('user_id', 'Unknown')}"
        )
        abort(403)

    data = request.values.to_dict()
    gm_id = data["gm_id"]
    logger.info(
        f"User {payload.get('user_id', 'Unknown')} is creating a game with GM ID {gm_id}"
    )

    game = build_game_from_form(data, gm_id)
    logger.info(f"Game object created: {game.name}")

    is_open = data["action"] == "open"
    if is_open:
        logger.info("Game is being posted as open.")
        setup_game_post_creation(game, bot)
        logger.info("Game post-creation setup completed.")

    try:
        db.session.add(game)
        db.session.commit()
        logger.info(f"Game saved in DB with ID: {game.id}")

        if is_open:
            game = db.get_or_404(Game, game.id)
            game.msg_id = send_discord_embed(game)
            db.session.commit()
            logger.info(f"Discord embed sent with message ID: {game.msg_id}")

    except Exception as e:
        logger.error(f"Failed to save game: {e}", exc_info=True)
        if is_open:
            logger.info("Rolling back channel and role creation due to error")
            rollback_discord_resources(bot, game)
        abort(500, e)

    return redirect(url_for("annonces.get_game_details", game_id=game.id))


@game_bp.route("/annonces/<game_id>/editer/", methods=["POST"])
@login_required
def edit_game(game_id):
    payload = who()
    data = request.values.to_dict()
    bot = get_bot()

    game = get_game_if_authorized(payload, game_id)
    gm_id = data["gm_id"]
    post = game.status == "draft" and data["action"] == "open"

    logger.info(f"Editing game {game.id} - Post: {post}")
    update_game_from_form(game, data)
    logger.info(f"Game {game.id} updated with new data")

    if post:
        logger.info(
            "Game was draft, setting to open and creating session/channel/role."
        )
        game.status = data["action"]
        setup_game_post_creation(game, bot)
        logger.info(f"Game {game.id} post-publishing setup completed.")

    try:
        if post:
            game.msg_id = send_discord_embed(game)
            logger.info(f"Embed sent for game {game.id}")

        db.session.commit()
        logger.info(f"Game {game.id} changes saved")
    except Exception as e:
        logger.error(f"Failed to edit game {game.id}: {e}", exc_info=True)
        if post:
            logger.info("Rolling back channel and role creation due to error")
            rollback_discord_resources(bot, game)
        abort(500, e)
    return redirect(url_for("annonces.get_game_details", game_id=game.id))


@game_bp.route("/annonces/<game_id>/statut/", methods=["POST"])
@login_required
def change_game_status(game_id):
    """
    Change game status and redirect to the game details.
    """
    payload = who()
    bot = get_bot()
    game = get_game_if_authorized(payload, game_id)
    status = request.values.to_dict()["status"]
    game.status = status
    create_game_event(game, "Status Update", status)
    try:
        db.session.commit()
        logger.info(f"Game status for {game.id} has been updated to {status}")
        if status == "archived":
            bot.delete_channel(game.channel)
            logger.info(f"Game {game.id} channel {game.channel} has been deleted")
            bot.delete_role(game.role)
            logger.info(f"Game {game.id} role {game.role} has been deleted")
    except Exception as e:
        abort(500, e)

    return redirect(url_for("annonces.get_game_details", game_id=game.id))


@game_bp.route("/annonces/<game_id>/sessions/ajouter", methods=["POST"])
@login_required
def add_game_session(game_id):
    """
    Add session to a game and redirect to the game details.
    """
    payload = who()
    game = get_game_if_authorized(payload, game_id)
    start = request.values.to_dict()["date_start"]
    end = request.values.to_dict()["date_end"]
    if start > end:
        abort(500, "Impossible d'ajouter une session qui se termine avant de commencer")
    create_game_session(
        game,
        start,
        end,
    )
    create_game_event(game, "Session Add", f"New session {start}/{end}")
    try:
        db.session.commit()
        logger.info(f"Session {start}/{end} created for Game {game.id}")
        send_discord_embed(
            game,
            type="add-session",
            start=datetime.strptime(start, DEFAULT_TIMEFORMAT).strftime(
                HUMAN_TIMEFORMAT
            ),
            end=datetime.strptime(end, DEFAULT_TIMEFORMAT).strftime(HUMAN_TIMEFORMAT),
        )
    except Exception as e:
        abort(500, e)
    return redirect(url_for("annonces.get_game_details", game_id=game_id))


@game_bp.route("/annonces/<game_id>/sessions/<session_id>/editer", methods=["POST"])
@login_required
def edit_game_session(game_id, session_id):
    """
    Edit game session and redirect to the game details.
    """
    payload = who()
    game = get_game_if_authorized(payload, game_id)
    session = db.get_or_404(GameSession, session_id)
    old_start = session.start.strftime(HUMAN_TIMEFORMAT)
    old_end = session.end.strftime(HUMAN_TIMEFORMAT)
    session.start = request.values.to_dict()["date_start"]
    session.end = request.values.to_dict()["date_end"]
    create_game_event(
        game, "Session Edit", f"{old_start}/{old_end} -> {session.start}/{session.end}"
    )
    if session.start > session.end:
        abort(500, "Impossible d'ajouter une session qui se termine avant de commencer")
    try:
        db.session.commit()
        logger.info(
            f"Session {old_start}/{old_end} of Game {game.id} has been updated to {session.start}/{session.end}"
        )
        send_discord_embed(
            game,
            type="edit-session",
            start=session.start.strftime(HUMAN_TIMEFORMAT),
            end=session.end.strftime(HUMAN_TIMEFORMAT),
            old_start=old_start,
            old_end=old_end,
        )
    except Exception as e:
        abort(500, e)
    return redirect(url_for("annonces.get_game_details", game_id=game_id))


@game_bp.route("/annonces/<game_id>/sessions/<session_id>/supprimer", methods=["POST"])
@login_required
def remove_game_session(game_id, session_id):
    """
    Remove session from a game and redirect to the game details.
    """
    payload = who()
    game = get_game_if_authorized(payload, game_id)
    session = db.get_or_404(GameSession, session_id)
    start = session.start
    end = session.end
    delete_game_session(session)
    create_game_event(game, "Session Delete", f"{start}/{end}")
    try:
        db.session.commit()
        logger.info(f"Session {start}/{end} of Game {game.id} has been removed")
        send_discord_embed(
            game,
            type="del-session",
            start=start.strftime(HUMAN_TIMEFORMAT),
            end=end.strftime(HUMAN_TIMEFORMAT),
        )
    except Exception as e:
        abort(500, e)
    return redirect(url_for("annonces.get_game_details", game_id=game_id))


@game_bp.route("/annonces/<game_id>/inscription/", methods=["POST"])
@login_required
def register_game(game_id):
    """Register a player to a game."""
    payload = who()
    user_id = payload["user_id"]
    bot = get_bot()
    game = db.get_or_404(Game, game_id)

    if game.status in ["closed", "archived"]:
        flash("Ce jeu est fermé aux inscriptions.", "warning")
        return redirect(url_for("annonces.get_game_details", game_id=game.id))

    if game.gm_id == user_id:
        flash("Vous ne pouvez pas vous inscrire à votre propre partie.", "warning")
        return redirect(url_for("annonces.get_game_details", game_id=game.id))

    user = db.get_or_404(User, user_id)
    try:
        register_user_to_game(game, user, bot)
    except ValueError as ve:
        flash(str(ve), "danger")
    except Exception as e:
        logger.exception("Registration failed")
        flash("Une erreur est survenue pendant l'inscription.", "danger")

    return redirect(url_for("annonces.get_game_details", game_id=game.id))


@game_bp.route("/annonces/<game_id>/gerer/", methods=["POST"])
@login_required
def manage_game_registration(game_id):
    """Manage player registration for a game."""
    payload = who()
    user_id = payload["user_id"]
    bot = get_bot()
    game = db.get_or_404(Game, game_id)

    if game.status == "archived":
        flash("Impossible de gérer les joueur·euses d'une partie archivée.", "danger")
        return redirect(url_for("annonces.get_game_details", game_id=game.id))
    if game.gm_id != user_id and not payload["is_admin"]:
        flash("Vous n'êtes pas autorisé·e à faire cette action.", "danger")
        return redirect(url_for("annonces.get_game_details", game_id=game.id))

    data = request.values.to_dict()
    action = data.get("action")

    try:
        if action == "manage":
            handle_remove_players(game, data, bot)
        elif action == "add":
            handle_add_player(game, data, bot)
        else:
            flash("Action demandée non gérée.", "danger")
            return redirect(url_for("annonces.get_game_details", game_id=game.id))
    except Exception as e:
        logger.exception("Error during game registration management")
        flash(f"Erreur pendant l'inscription: {e}.", "danger")
        return redirect(url_for("annonces.get_game_details", game_id=game.id))

    return redirect(url_for("annonces.get_game_details", game_id=game.id))


@game_bp.route("/annonces/<game_id>/editer/", methods=["GET"])
@login_required
def get_game_edit_form(game_id):
    """
    Get form to edit a game.
    """
    payload = who()
    game = get_game_if_authorized(payload, game_id)
    return render_template(
        "game_form.j2",
        payload=payload,
        game=game,
        systems=System.get_systems(),
        vtts=Vtt.get_vtts(),
    )


@game_bp.route("/mes_annonces/", methods=["GET"])
@login_required
def my_gm_games():
    """
    List all of games where current user is GM.
    """
    payload = who()
    abort_if_not_gm(payload)
    try:
        games_as_gm = db.session.get(User, payload["user_id"]).games_gm
    except AttributeError:
        games_as_gm = {}
    return render_template(
        GAME_LIST_TEMPLATE,
        payload=payload,
        games=games_as_gm,
        gm_only=True,
        title="Mes annonces",
    )


@game_bp.route("/mes_parties/", methods=["GET"])
@login_required
def my_games():
    """
    List all of current user non archived games "as player"
    """
    payload = who()
    try:
        user = db.session.get(User, payload["user_id"])
        games = user.games
        active_games = []
        for game in games:
            if game.status != "archived":
                active_games.append(game)
    except AttributeError:
        games = {}
    return render_template(
        GAME_LIST_TEMPLATE,
        payload=payload,
        games=active_games,
        title="Mes parties en cours",
    )
