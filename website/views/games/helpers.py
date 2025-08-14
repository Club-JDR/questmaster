from flask import abort, flash, redirect, url_for, request, current_app
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import case
from sqlalchemy.sql import func, or_, and_
from website.utils.logger import logger, log_game_event
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


def parse_multi_checkbox_filter(source, keys):
    filters = []
    args = {}
    for key in keys:
        if source.get(key, type=bool):
            filters.append(key)
            args[key] = "on"
    return filters, args


def build_base_filters(request_args, name, system, vtt):
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


def build_status_filters(statuses, user_payload):
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


def get_filtered_games(
    request_args_source,
    base_query=None,
    default_status=None,
    default_type=None,
    default_restriction=None,
):
    request_args = {}
    now = datetime.now(timezone.utc)
    user_payload = who()

    # Parse filters
    status, status_args = parse_multi_checkbox_filter(
        request_args_source, ["open", "closed", "archived", "draft"]
    )
    game_type, type_args = parse_multi_checkbox_filter(
        request_args_source, ["oneshot", "campaign"]
    )
    restriction, restriction_args = parse_multi_checkbox_filter(
        request_args_source, ["all", "16+", "18+"]
    )
    request_args.update(status_args)
    request_args.update(type_args)
    request_args.update(restriction_args)

    # Normalize defaults
    status, game_type, restriction = set_default_search_parameters(
        status,
        game_type,
        restriction,
        default_status=default_status,
        default_type=default_type,
        default_restriction=default_restriction,
    )

    # Build queries
    queries = [
        Game.restriction.in_(restriction),
        Game.type.in_(game_type),
    ]

    name = request_args_source.get("name", type=str)
    system = request_args_source.get("system", type=int)
    vtt = request_args_source.get("vtt", type=int)
    queries += build_base_filters(request_args, name, system, vtt)
    queries.append(build_status_filters(status, user_payload))

    # Sorting
    status_order = case(
        (Game.status == "draft", 0),
        (Game.status == "open", 1),
        (Game.status == "closed", 2),
        (Game.status == "archived", 3),
    )
    is_future = case((Game.date >= now, 0), else_=1)
    time_distance = func.abs(func.extract("epoch", Game.date - now))

    # Pagination
    page = request_args_source.get("page", 1, type=int)
    query = base_query or Game.query
    games = (
        query.filter(*queries)
        .order_by(status_order, is_future, time_distance)
        .paginate(page=page, per_page=GAMES_PER_PAGE, error_out=False)
    )

    return games, request_args


def get_filtered_user_games(request_args_source, user_id, role="gm"):
    user = db.session.get(User, user_id)
    if not user:
        return [], {}

    if role == "gm":
        base_query = Game.query.filter(Game.gm_id == user_id)
    elif role == "player":
        game_ids = [game.id for game in user.games]
        base_query = Game.query.filter(Game.id.in_(game_ids))
    else:
        raise ValueError("Invalid role passed to get_filtered_user_games")

    return get_filtered_games(
        request_args_source,
        base_query,
        default_status=["draft", "open", "closed", "archived"],  # All statuses
    )


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
    game.sessions.append(session)
    db.session.commit()
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


def set_default_search_parameters(
    status,
    game_type,
    restriction,
    default_status=None,
    default_type=None,
    default_restriction=None,
):
    if not status:
        status = default_status or ["open"]
    if not game_type:
        game_type = default_type or ["oneshot", "campaign"]
    if not restriction:
        restriction = default_restriction or ["all", "16+", "18+"]
    return status, game_type, restriction


def get_classification():
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
    for player in game.players:
        if str(player.id) not in data:
            game.players.remove(player)
            logger.info(f"User {player.id} removed from Game {game.id}")
            bot.remove_role_from_user(player.id, game.role)
            logger.info(f"Role {game.role} removed from Player {player.id}")
            removed = True
            log_game_event(
                "unregister",
                game.id,
                f"{player} a été désinscrit de l'annonce.",
            )
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

    user.refresh_roles()
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
            if game.msg_id:
                try:
                    send_discord_embed(game, type="annonce")
                    logger.info(
                        f"Embed updated due to status change for game {game.id}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to update embed on status change for game {game.id}: {e}"
                    )
            log_game_event(
                "edit",
                game.id,
                f"Annonce fermée automatiquement après avoir atteint le nombre max de joueur·euses ({game.party_size}).",
            )
            logger.info(f"Game status for {game.id} has been updated to closed")
        db.session.commit()
        if force:
            log_game_event(
                "register",
                game.id,
                f"{user.display_name} a été inscrit à l'annonce par le MJ ou un admin.",
            )
        else:
            log_game_event(
                "register", game.id, f"{user.display_name} s'est inscrit sur l'annonce."
            )
        logger.info(f"User {user.id} registered to Game {game.id}")
        bot.add_role_to_user(user.id, game.role)
        logger.info(f"Role {game.role} added to user {user.id}")
        send_discord_embed(game, type="register", player=user.id)
    except SQLAlchemyError:
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
        classification=get_classification(),
        ambience=get_ambience(data),
        complement=data.get("complement"),
        status="closed" if data["action"] == "open-silent" else data["action"],
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
    game.classification = get_classification()
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
        role_name="PJ_" + game.slug,
        permissions=PLAYER_ROLE_PERMISSION,
        color=Game.COLORS[game.type],
    )["id"]
    logger.info(f"Role created with ID: {game.role}")

    category = get_channel_category(game)
    game.channel = bot.create_channel(
        channel_name=game.slug.lower(),
        parent_id=category.id,
        role_id=game.role,
        gm_id=game.gm_id,
    )["id"]
    logger.info(
        f"Channel created with ID: {game.channel} under category: {category.id}"
    )
    category.size += 1
    send_discord_embed(game, type="annonce_details")


def rollback_discord_resources(bot, game):
    if game.channel:
        bot.delete_channel(game.channel)
        logger.info(f"Channel {game.channel} deleted")
    if game.role:
        bot.delete_role(game.role)
        logger.info(f"Role {game.role} deleted")


def add_trophy_to_user(user_id, trophy_id, amount=1):
    trophy = db.session.get(Trophy, trophy_id)
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


def award_game_trophies(game):
    trophy_map = {
        "oneshot": (BADGE_OS_GM_ID, BADGE_OS_ID),
        "campaign": (BADGE_CAMPAIGN_GM_ID, BADGE_CAMPAIGN_ID),
    }
    gm_trophy, player_trophy = trophy_map.get(game.type, (None, None))
    if gm_trophy:
        add_trophy_to_user(user_id=game.gm.id, trophy_id=gm_trophy)
        for user in game.players:
            add_trophy_to_user(user_id=user.id, trophy_id=player_trophy)


def adjust_category_size(bot, game):
    try:
        discord_channel = bot.get_channel(game.channel)
        parent_id = discord_channel.get("parent_id")
        if parent_id:
            category = Channel.query.filter_by(id=parent_id).first()
            if category:
                category.size = max(0, category.size - 1)
                db.session.commit()
                logger.info(
                    f"Decreased size of category {category.id} to {category.size}"
                )
    except Exception as e:
        logger.warning(f"Failed to adjust category size for game {game.id}: {e}")


def delete_discord_resources(bot, game):
    bot.delete_channel(game.channel)
    logger.info(f"Game {game.id} channel {game.channel} has been deleted")
    bot.delete_role(game.role)
    logger.info(f"Game {game.id} role {game.role} has been deleted")


def delete_game_message(bot, game):
    if not game.msg_id:
        return
    try:
        bot.delete_message(game.msg_id, current_app.config["POSTS_CHANNEL_ID"])
        game.msg_id = None
        db.session.commit()
        logger.info(f"Discord embed message deleted for archived game {game.id}")
    except Exception as e:
        logger.warning(f"Failed to delete message for archived game {game.id}: {e}")


def archive_game(game, bot, award_trophies=True):
    msg = "Annonce archivée."
    if award_trophies:
        award_game_trophies(game)
        msg += " Badges distribués."
    else:
        msg += " Badges non-distribués."
    adjust_category_size(bot, game)
    delete_discord_resources(bot, game)
    log_game_event("delete", game.id, msg)
    delete_game_message(bot, game)
