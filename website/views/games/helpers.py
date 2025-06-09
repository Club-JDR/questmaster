from flask import abort, flash, redirect, url_for, request
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from website.utils.logger import logger
from website.extensions import db
from website.models import (
    Game,
    GameSession,
    Channel,
    User,
    Trophy,
    UserTrophy,
)
from website.utils.discord import PLAYER_ROLE_PERMISSION
from website.views.games.embeds import send_discord_embed, DEFAULT_TIMEFORMAT
from website.views.auth import who
from website.models.trophy import (
    BADGE_OS_ID,
    BADGE_OS_GM_ID,
    BADGE_CAMPAIGN_ID,
    BADGE_CAMPAIGN_GM_ID,
)
from slugify import slugify
from config import GAME_DETAILS_ROUTE, GAMES_PER_PAGE
import yaml


def generate_game_slug(name, gm_name, existing_slugs):
    base_slug = slugify(f"{name}-par-{gm_name}")
    slug = base_slug
    i = 2
    while slug in existing_slugs:
        slug = f"{base_slug}-{i}"
        i += 1
    return slug


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


def get_game_if_authorized(payload, slug):
    """
    Return game if user is either the game's GM or admin
    """
    game = Game.query.filter_by(slug=slug).first_or_404()
    if game.gm_id != payload["user_id"] and not payload["is_admin"]:
        flash("Seul·e le·a MJ de l'annonce peut faire cette opération.", "danger")
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=slug))
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
        return redirect(url_for(GAME_DETAILS_ROUTE, slug=game.slug))

    payload = who()
    force = payload["user_id"] == game.gm.id or payload.get("is_admin", False)

    register_user_to_game(game, user, bot, force=force)


def register_user_to_game(original_game, user, bot, force=False):
    """Concurrent-safe logic to register a user to a game and update state."""
    try:
        game = (
            db.session.query(Game)
            .filter_by(id=original_game.id)
            .with_for_update()
            .first()
        )
        game = db.session.query(Game).filter_by(id=original_game.id).first()
        if user in game.players:
            logger.warning(f"User {user.id} already in Game {game.id}")
            return
        if len(game.players) >= game.party_size and not force:
            logger.warning(f"Game {game.id} is full. Cannot add user {user.id}")
            flash("La partie est complète.", "danger")
            return redirect(url_for(GAME_DETAILS_ROUTE, slug=game.slug))
        if game.status == "closed" and not force:
            logger.warning(f"Game {game.id} is closed. Cannot add user {user.id}")
            flash("La partie est fermée.", "danger")
            return redirect(url_for(GAME_DETAILS_ROUTE, slug=game.slug))
        game.players.append(user)
        if len(game.players) >= game.party_size and not game.party_selection:
            game.status = "closed"
        db.session.commit()
        logger.info(f"User {user.id} registered to Game {game.id}")
        if game.status == "closed":
            logger.info(f"Game status for {game.id} has been updated to closed")
        bot.add_role_to_user(user.id, game.role)
        logger.info(f"Role {game.role} added to user {user.id}")
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
        status="open" if data["action"] == "open-silent" else data["action"],
        img=data.get("img"),
    )
    existing_slugs = {g.slug for g in Game.query.with_entities(Game.slug).all()}
    gm_name = db.get_or_404(User, str(gm_id)).name
    game.slug = generate_game_slug(data["name"], gm_name, existing_slugs)
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


def add_trophy_to_user(user_id, trophy_id, amount=1):
    trophy = Trophy.query.get(trophy_id)
    if not trophy:
        return

    user_trophy = UserTrophy.query.filter_by(
        user_id=user_id, trophy_id=trophy_id
    ).first()

    if trophy.unique:
        if user_trophy is None:
            user_trophy = UserTrophy(user_id=user_id, trophy_id=trophy_id, quantity=1)
            db.session.add(user_trophy)
        else:
            # Do nothing if already has it
            return
    else:
        if user_trophy:
            user_trophy.quantity += amount
        else:
            user_trophy = UserTrophy(
                user_id=user_id, trophy_id=trophy_id, quantity=amount
            )
            db.session.add(user_trophy)
    db.session.commit()
    logger.info(f"User {user_id} got a trophy: {trophy.name}")


def archive_game(game, bot):
    if game.type == "oneshot":
        add_trophy_to_user(user_id=game.gm.id, trophy_id=BADGE_OS_GM_ID)
        for user in game.players:
            add_trophy_to_user(user_id=user.id, trophy_id=BADGE_OS_ID)
    elif game.type == "campaign":
        add_trophy_to_user(user_id=game.gm.id, trophy_id=BADGE_CAMPAIGN_GM_ID)
        for user in game.players:
            add_trophy_to_user(user_id=user.id, trophy_id=BADGE_CAMPAIGN_ID)
    bot.delete_channel(game.channel)
    logger.info(f"Game {game.id} channel {game.channel} has been deleted")
    bot.delete_role(game.role)
    logger.info(f"Game {game.id} role {game.role} has been deleted")
