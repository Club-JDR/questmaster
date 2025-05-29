from flask import abort
from website.utils.logger import logger
from website.extensions import db
from website.models import Game, GameSession, GameEvent, Channel, User
from website.utils.discord import PLAYER_ROLE_PERMISSION
from .embeds import send_discord_embed, DEFAULT_TIMEFORMAT
from datetime import datetime, timedelta
import yaml


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
    classification = {}
    for theme in ["action", "investigation", "interaction", "horror"]:
        if data.get(f"class-{theme}") == "none":
            classification[theme] = 0
        elif data.get(f"class-{theme}") == "min":
            classification[theme] = 1
        elif data.get(f"class-{theme}") == "maj":
            classification[theme] = 2
    if all(value == 0 for value in classification.values()):
        return None
    return classification


def get_ambience(data):
    ambience = []
    for a in ["chill", "serious", "comic", "epic"]:
        if data.get(a):
            ambience.append(a)
    return ambience


def handle_remove_players(game, data, bot):
    """Remove unchecked players from the game."""
    for player in list(game.players):  # Copy to avoid mutation during iteration
        if str(player.id) not in data:
            user = db.get_or_404(User, player.id)
            game.players.remove(user)
            create_game_event(game, "Remove Player", user.id)
            db.session.commit()
            logger.info(f"User {user.id} removed from Game {game.id}")
            bot.remove_role_from_user(user.id, game.role)
            logger.info(f"Role {game.role} removed from Player {user.id}")


def handle_add_player(game, data, bot):
    """Add a new player to the game."""
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
        abort(500, "Cette personne n'est pas un·e joueur·euse sur le Discord")

    game.players.append(user)
    create_game_event(game, "Add Player", uid)
    db.session.commit()
    logger.info(f"User {uid} registered to Game {game.id}")
    bot.add_role_to_user(uid, game.role)
    logger.info(f"Role {game.role} added to user {uid}")
    send_discord_embed(game, type="register", player=uid)


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
