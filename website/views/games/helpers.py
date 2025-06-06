from flask import abort, flash, redirect, url_for, request
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from website.utils.logger import logger
from website.extensions import db
from website.models import Game, GameSession, GameEvent, Channel, User
from website.utils.discord import PLAYER_ROLE_PERMISSION
from .embeds import send_discord_embed, DEFAULT_TIMEFORMAT
import yaml


GAMES_PER_PAGE = 12


def get_filtered_games(request_args_source):
    """
    Extracts filters from request args, builds a query, and returns paginated games and request_args.
    """
    status = []
    game_type = []
    restriction = []
    request_args = {}

    name = request_args_source.get("name", type=str)
    system = request_args_source.get("system", type=int)
    vtt = request_args_source.get("vtt", type=int)

    for s in ["open", "closed", "archived", "draft"]:
        if request_args_source.get(s, type=bool):
            status.append(s)
            request_args[s] = "on"
    for t in ["oneshot", "campaign"]:
        if request_args_source.get(t, type=bool):
            game_type.append(t)
            request_args[t] = "on"
    for r in ["all", "16+", "18+"]:
        if request_args_source.get(r, type=bool):
            restriction.append(r)
            request_args[r] = "on"

    status, game_type, restriction = set_default_search_parameters(
        status, game_type, restriction
    )

    queries = [
        Game.status.in_(status),
        Game.restriction.in_(restriction),
        Game.type.in_(game_type),
    ]
    if name:
        request_args["name"] = name
        queries.append(Game.name.ilike(f"%{name}%"))
    if system:
        request_args["system"] = system
        queries.append(Game.system_id == system)
    if vtt:
        request_args["vtt"] = vtt
        queries.append(Game.vtt_id == vtt)

    page = request_args_source.get("page", 1, type=int)

    games = (
        Game.query.filter(*queries)
        .order_by(Game.date)
        .paginate(page=page, per_page=GAMES_PER_PAGE, error_out=False)
    )

    return games, request_args


def get_channel_category(game):
    if game.type == "oneshot":
        category = (
            Channel.query.filter_by(type="oneshot").order_by(Channel.size).first()
        )
    else:
        category = (
            Channel.query.filter_by(type="campaign").order_by(Channel.size).first()
        )
    return category


def abort_if_not_gm(payload):
    """
    Return 403 if user is not GM
    """
    if not payload["is_gm"]:
        abort(403)


def get_game_if_authorized(payload, game_id):
    """
    Return game if user is either the game's GM or admin
    """
    game = db.get_or_404(Game, game_id)
    if game.gm_id != payload["user_id"] and not payload["is_admin"]:
        abort(403)
    return game


def create_game_session(game, start, end):
    """
    Create a session for a game.
    """
    session = GameSession(start=start, end=end)
    db.session.add(session)
    db.session.commit()
    game.sessions.append(session)
    logger.info(f"Session added for game {game.id} from {start} to {end}")


def create_game_event(game, type, description=None):
    """
    Create an event for a game.
    """
    event = GameEvent(event_type=type, description=description)
    db.session.add(event)
    db.session.commit()
    game.events.append(event)


def delete_game_session(session):
    """
    Delete a session for a game.
    """
    db.session.delete(session)
    db.session.commit()
    logger.info(
        f"Session removed for game {session.game_id} from {session.start} to {session.end}"
    )


def set_default_search_parameters(status, game_type, restriction):
    if len(status) == 0:
        status = ["open"]
    if len(game_type) == 0:
        game_type = ["oneshot", "campaign"]
    if len(restriction) == 0:
        restriction = ["all", "16+", "18+"]
    return status, game_type, restriction


def get_classification(data):
    prefix = "class-"
    classification = {}
    for key in request.form:
        if key.startswith(prefix):
            clean_key = key[len(prefix) :]
            try:
                classification[clean_key] = int(request.form[key])
            except (ValueError, TypeError):
                classification[clean_key] = 0
    return classification


def get_ambience(data):
    ambience = []
    for a in ["chill", "serious", "comic", "epic"]:
        if data.get(a):
            ambience.append(a)
    return ambience


def handle_remove_players(game, data, bot):
    """Remove unchecked players from the game."""
    removed = False
    for player in list(game.players):
        if str(player.id) not in data:
            game.players.remove(player)
            create_game_event(game, "Remove Player", player.id)
            logger.info(f"User {player.id} removed from Game {game.id}")
            bot.remove_role_from_user(player.id, game.role)
            logger.info(f"Role {game.role} removed from Player {player.id}")
            removed = True
    if removed:
        db.session.commit()


def handle_add_player(game, data, bot):
    """Add a new player to the game by Discord ID."""
    uid = data.get("discord_id")
    if not uid:
        abort(400, "Missing discord_id")

    user = db.session.get(User, str(uid))
    if not user:
        user = User(id=str(uid))
        db.session.add(user)
        db.session.commit()
        logger.info(f"User {uid} created in database")
        user.init_on_load()

    if not user.is_player:
        flash("Cette personne n'est pas un·e joueur·euse sur le Discord", "danger")
        return redirect(url_for("annonces.get_game_details", game_id=game.id))

    register_user_to_game(game, user, bot)


def register_user_to_game(original_game, user, bot):
    """Concurrent-safe logic to register a user to a game and update state."""
    try:
        # Lock the game row and load players in a separate transaction.
        game = (
            db.session.query(Game)
            .filter_by(id=original_game.id)
            .with_for_update()
            .first()
        )

        # Make sure to reload players in a separate query (without joinedload).
        game = db.session.query(Game).filter_by(id=original_game.id).first()

        # Check if the user is already in the game
        if user in game.players:
            logger.warning(f"User {user.id} already in Game {game.id}")
            return  # No-op if already registered

        # Check if the game is full
        if len(game.players) >= game.party_size:
            logger.warning(f"Game {game.id} is full. Cannot add user {user.id}")
            flash("La partie est complète.", "danger")
            return redirect(url_for("annonces.get_game_details", game_id=game.id))

        # Add the player to the game
        game.players.append(user)
        create_game_event(game, "Add Player", user.id)

        # Update game status to 'closed' if full and no party selection
        if len(game.players) == game.party_size and not game.party_selection:
            game.status = "closed"
            create_game_event(game, "Status Update", "closed")

        # Commit the transaction
        db.session.commit()

        logger.info(f"User {user.id} registered to Game {game.id}")
        if game.status == "closed":
            logger.info(f"Game status for {game.id} has been updated to closed")

        # Add role to user via the bot
        bot.add_role_to_user(user.id, game.role)
        logger.info(f"Role {game.role} added to user {user.id}")

        # Send Discord embed notification
        send_discord_embed(game, type="register", player=user.id)

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.exception("Failed to register user due to DB error.")
        raise


def build_game_from_form(data, gm_id):
    game = Game(
        name=data["name"],
        type=data["type"],
        length=data["length"],
        gm_id=gm_id,
        system_id=data["system"],
        vtt_id=data["vtt"] or None,
        description=data["description"],
        restriction=data["restriction"],
        party_size=data["party_size"],
        xp=data["xp"],
        date=datetime.strptime(data["date"], DEFAULT_TIMEFORMAT),
        session_length=data["session_length"],
        frequency=data.get("frequency") or None,
        characters=data["characters"],
        classification=get_classification(data),
        ambience=get_ambience(data),
        complement=data.get("complement"),
        status=data["action"],
        img=data.get("img"),
    )
    game.party_selection = "party_selection" in data
    game.restriction_tags = parse_restriction_tags(data)
    return game


def update_game_from_form(game, data):
    if game.status == "draft":
        game.name = data["name"]
        game.type = data["type"]
    game.system_id = data["system"]
    game.vtt_id = data["vtt"] or None
    game.description = data["description"]
    game.date = datetime.strptime(data["date"], DEFAULT_TIMEFORMAT)
    game.length = data["length"]
    game.party_size = data["party_size"]
    game.party_selection = "party_selection" in data
    game.xp = data["xp"]
    game.session_length = data["session_length"]
    game.frequency = data.get("frequency") or None
    game.characters = data["characters"]
    game.classification = get_classification(data)
    game.ambience = get_ambience(data)
    game.complement = data.get("complement")
    game.img = data.get("img")
    game.restriction = data["restriction"]
    game.restriction_tags = parse_restriction_tags(data)


def parse_restriction_tags(data):
    raw = data.get("restriction_tags", "")
    if not raw:
        return None
    try:
        tags = yaml.safe_load(raw)
        return ", ".join(item["value"] for item in tags)
    except Exception as e:
        logger.warning(f"Failed to parse restriction tags: {e}", exc_info=True)
        return None


def setup_game_post_creation(game, bot):
    create_game_session(
        game,
        game.date,
        game.date + timedelta(hours=float(game.session_length)),
    )
    logger.info("Initial game session created.")

    create_game_event(game, "Game Creation")
    logger.info("Initial game event registered.")

    game.role = bot.create_role(
        role_name=game.name,
        permissions=PLAYER_ROLE_PERMISSION,
        color=Game.COLORS[game.type],
    )["id"]
    logger.info(f"Role created with ID: {game.role}")

    category = get_channel_category(game)
    game.channel = bot.create_channel(
        channel_name=game.name.lower(),
        parent_id=category.id,
        role_id=game.role,
        gm_id=game.gm_id,
    )["id"]
    logger.info(
        f"Channel created with ID: {game.channel} under category: {category.id}"
    )

    category.size += 1


def rollback_discord_resources(bot, game):
    if game.channel:
        bot.delete_channel(game.channel)
        logger.info(f"Channel {game.channel} deleted")
    if game.role:
        bot.delete_role(game.role)
        logger.info(f"Role {game.role} deleted")
