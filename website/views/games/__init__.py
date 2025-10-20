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
from config import SEARCH_GAMES_ROUTE, GAME_DETAILS_ROUTE
from website.extensions import db
from website.bot import get_bot
from website.models import Game, User, System, Vtt, GameSession, SpecialEvent
from website.views.auth import who, login_required
from website.utils.logger import logger, log_game_event
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
    event = db.session.get(SpecialEvent, event_id)
    if not event:
        flash("L'événement demandé n'existe pas.", "warning")
        return redirect(url_for(SEARCH_GAMES_ROUTE))

    base_query = Game.query.filter(Game.special_event_id == event_id)

    games, request_args = get_filtered_games(
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
    games, _ = get_filtered_games(request.args)
    return render_template("game_cards_container.j2", games=games.items)


@game_bp.route("/annonces/<slug>/", methods=["GET"])
def get_game_details(slug):
    """
    Get details for a given game.
    """
    payload = who()
    game = Game.query.filter_by(slug=slug).first_or_404()
    is_player = False
    for player in game.players:
        if "user_id" in payload and payload["user_id"] == player.id:
            is_player = True
    return render_template("game_details.j2", game=game, is_player=is_player)


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
        flash("Vous devez être MJ pour poster une annonce.", "danger")
        return redirect(url_for(SEARCH_GAMES_ROUTE))

    data = request.values.to_dict()
    gm_id = data["gm_id"]
    logger.info(
        f"User {payload.get('user_id', 'Unknown')} is creating a game with GM ID {gm_id}"
    )
    game = build_game_from_form(data, gm_id)
    logger.info(f"Game object created: {game.name}")
    msg = f"Annonce {game.name} enregistrée."
    post = data["action"] in ("open", "open-silent")
    if post:
        logger.info(f"Game is being posted as {data['action']}.")
        setup_game_post_creation(game, bot)
        logger.info("Game post-creation setup completed.")
        msg = f"Annonce {game.name} postée."

    try:
        db.session.add(game)
        db.session.commit()
        log_game_event(
            "create",
            game.id,
            f"Annonce créée avec le statut {game.status}.",
        )
        logger.info(f"Game saved in DB with ID: {game.id}")

        if post and data["action"] == "open":
            game = db.get_or_404(Game, game.id)
            game.msg_id = send_discord_embed(game)
            db.session.commit()
            logger.info(f"Discord embed sent with message ID: {game.msg_id}")

    except Exception as e:
        logger.error(f"Failed to save game: {e}", exc_info=True)
        if post and data["action"] == "open-silent":
            logger.info("Rolling back channel and role creation due to error")
            rollback_discord_resources(bot, game)
        flash("Une erreur est survenue pendant la création de l'annonce.", "danger")
        return redirect(url_for(SEARCH_GAMES_ROUTE))
    flash(msg, "success")
    return redirect(url_for(GAME_DETAILS_ROUTE, slug=game.slug))


@game_bp.route("/annonces/<slug>/editer/", methods=["POST"])
@login_required
def edit_game(slug):
    payload = who()
    data = request.values.to_dict()
    bot = get_bot()

    game = get_game_if_authorized(payload, slug)
    post = game.status == "draft" and data["action"] in ("open", "open-silent")

    logger.info(f"Editing game {game.id} - Post: {post}")
    update_game_from_form(game, data)
    logger.info(f"Game {game.id} updated with new data")
    msg = "Annonce modifiée."
    if post:
        logger.info(
            "Game was draft, setting to open and creating session/channel/role."
        )
        game.status = "open" if data["action"] == "open-silent" else data["action"]
        setup_game_post_creation(game, bot)
        logger.info(f"Game {game.id} post-publishing setup completed.")
        if data["action"] == "open-silent":
            msg = "Annonce modifiée et ouverte."
        else:
            msg = "Annonce modifiée et postée."
    try:
        if post and data["action"] == "open":
            game.msg_id = send_discord_embed(game)
            logger.info(f"Embed sent for game {game.id}")

        db.session.commit()
        log_game_event(
            "edit",
            game.id,
            "Le contenu de l'annonce a été édité.",
        )
        logger.info(f"Game {game.id} changes saved")
    except Exception as e:
        logger.error(f"Failed to edit game {game.id}: {e}", exc_info=True)
        if post:
            logger.info("Rolling back channel and role creation due to error")
            rollback_discord_resources(bot, game)
        flash("Une erreur est survenue pendant l'enregistrement.", "danger")
    if game.msg_id:
        try:
            send_discord_embed(game, type="annonce")
            logger.info(f"Embed updated for game {game.id}")
        except Exception as e:
            logger.warning(f"Failed to update Discord embed for game {game.id}: {e}")
    flash(msg, "success")
    return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))


@game_bp.route("/annonces/<slug>/statut/", methods=["POST"])
@login_required
def change_game_status(slug):
    """
    Change game status and redirect to the game details.
    """
    payload = who()
    bot = get_bot()
    game = get_game_if_authorized(payload, slug)
    status = request.values.get("status")
    award_trophies = "award_trophies" in request.form

    if status == "deleted":
        try:
            Game.query.filter(Game.id == game.id).delete()
            db.session.commit()
            logger.info(f"Game {game.id} has been deleted.")
            flash("Annonce supprimée avec succès.", "success")
        except Exception as e:
            flash("Une erreur est survenue pendant la suppression.", "danger")
            logger.error(e)
        return redirect("/")

    if status == "publish":
        if game.msg_id:
            flash("Annonce déjà publiée.", "danger")
        elif len(game.players) >= game.party_size:
            flash("Impossible de publier une annonce complète.", "danger")
        else:
            try:
                game.status = "open"
                message_id = send_discord_embed(game, type="annonce")
                game.msg_id = message_id
                db.session.commit()
                logger.info(f"Game {game.id} published and opened.")
                log_game_event(
                    "edit",
                    game.id,
                    "L'annonce a été publiée et ouverte.",
                )
                flash("Annonce publiée avec succès.", "success")
            except Exception as e:
                logger.error(f"Failed to publish game {game.id}: {e}")
                flash("Une erreur est survenue pendant la publication.", "danger")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))

    game.status = status

    try:
        db.session.commit()
        log_game_event(
            "edit",
            game.id,
            f"Le statut de l'annonce à changé en {status}.",
        )
        logger.info(f"Game status for {game.id} has been updated to {status}")
        if status == "archived":
            archive_game(game, bot, award_trophies=award_trophies)
        elif game.msg_id:
            try:
                send_discord_embed(game, type="annonce")
                logger.info(f"Embed updated due to status change for game {game.id}")
            except Exception as e:
                logger.warning(
                    f"Failed to update embed on status change for game {game.id}: {e}"
                )
    except Exception:
        flash("Une erreur est survenue pendant la modification de statut.", "danger")
    status_msg = ""
    if status == "open":
        status_msg = "ouverte"
    elif status == "closed":
        status_msg = "fermée"
    elif status == "archived":
        status_msg = "archivée"
    flash(f"Annonce {game.name} {status_msg}.", "success")
    return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))


@game_bp.route("/annonces/<slug>/alert/", methods=["POST"])
@login_required
def send_alert(slug):
    """
    Send an alert message to the Discord channel and register a game event.
    """
    payload = who()
    game = Game.query.filter_by(slug=slug).first_or_404()

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
    except Exception as e:
        flash("Une erreur est survenue lors du signalement.", "danger")
        logger.error(f"Failed to send alert: {e}", exc_info=True)

    return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))


@game_bp.route("/annonces/<slug>/sessions/ajouter/", methods=["POST"])
@login_required
def add_game_session(slug):
    """
    Add session to a game and redirect to the game details.
    """
    payload = who()
    game = get_game_if_authorized(payload, slug)
    start = datetime.strptime(request.values.get("date_start"), DEFAULT_TIMEFORMAT)
    end = datetime.strptime(request.values.get("date_end"), DEFAULT_TIMEFORMAT)
    if start > end:
        flash(
            "Impossible d'ajouter une session qui se termine avant de commencer",
            "danger",
        )
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))
    try:
        create_game_session(
            game,
            start,
            end,
        )
        db.session.commit()
        log_game_event(
            "create-session",
            game.id,
            f"Une session a été créée de {start} à {end}.",
        )
        logger.info(f"Session {start}/{end} created for Game {game.id}")
        send_discord_embed(
            game,
            type="add-session",
            start=start,
            end=end,
        )
        flash("Session ajoutée.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception:
        db.session.rollback()
        flash("Une erreur est survenue pendant la création de la session.", "danger")

    return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))


@game_bp.route("/annonces/<slug>/sessions/<session_id>/editer/", methods=["POST"])
@login_required
def edit_game_session(slug, session_id):
    """
    Edit game session and redirect to the game details.
    """
    payload = who()
    game = get_game_if_authorized(payload, slug)
    session = db.get_or_404(GameSession, session_id)

    new_start = datetime.strptime(request.values.get("date_start"), DEFAULT_TIMEFORMAT)
    new_end = datetime.strptime(request.values.get("date_end"), DEFAULT_TIMEFORMAT)

    if new_start >= new_end:
        flash(
            "Impossible d'ajouter une session qui se termine avant de commencer.",
            "danger",
        )
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))

    if has_session_conflict(game, new_start, new_end, exclude_session_id=session.id):
        flash("Cette session chevauche une autre session du même jeu.", "danger")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))

    old_start = session.start.strftime(HUMAN_TIMEFORMAT)
    old_end = session.end.strftime(HUMAN_TIMEFORMAT)

    session.start = new_start
    session.end = new_end

    try:
        db.session.commit()
        log_game_event(
            "edit-session",
            game.id,
            f"Une session a été éditée : {old_start} → {old_end}, remplacée par {session.start} → {session.end}.",
        )
        logger.info(
            f"Session {old_start}/{old_end} of Game {game.slug} updated to {session.start}/{session.end}"
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
    except Exception:
        db.session.rollback()
        flash("Erreur lors de la modification de la session.", "danger")

    return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))


@game_bp.route("/annonces/<slug>/sessions/<session_id>/supprimer/", methods=["POST"])
@login_required
def remove_game_session(slug, session_id):
    """
    Remove session from a game and redirect to the game details.
    """
    payload = who()
    game = get_game_if_authorized(payload, slug)
    session = db.get_or_404(GameSession, session_id)
    start = session.start
    end = session.end
    delete_game_session(session)
    try:
        db.session.commit()
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
    game = Game.query.filter_by(slug=slug).first_or_404()

    if game.status in ["closed", "archived"]:
        flash("Ce jeu est fermé aux inscriptions.", "warning")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))

    if game.gm_id == user_id:
        flash("Vous ne pouvez pas vous inscrire à votre propre partie.", "warning")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))

    user = db.get_or_404(User, user_id)
    try:
        force = False
        if game.party_selection:
            force = True
        register_user_to_game(game, user, bot, force)
        flash("Vous êtes inscrit·e.", "success")
    except ValueError as ve:
        flash(str(ve), "danger")
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
    game = Game.query.filter_by(slug=slug).first_or_404()

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
            handle_remove_players(game, data, bot)
        elif action == "add":
            handle_add_player(game, data, bot)
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
    """
    Get form to edit or clone a game.
    """
    payload = who()
    game = get_game_if_authorized(payload, slug)
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
    """
    List all of games where current user is GM.
    """
    payload = who()
    abort_if_not_gm(payload)
    games, request_args = get_filtered_user_games(
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
    """
    List all of current user non archived games "as player"
    """
    payload = who()
    games, request_args = get_filtered_user_games(
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
