from flask import (
    request,
    current_app,
    render_template,
    redirect,
    url_for,
    abort,
)
from website import app, db, bot
from website.models import Game, User, System, Vtt, Session, Channel
from website.views.auth import who, login_required
from website.utils.discord import PLAYER_ROLE_PERMISSION
from sqlalchemy import func

from datetime import datetime, timedelta
import re, yaml, locale

GAMES_PER_PAGE = 12
GAME_LIST_TEMPLATE = "games.html"

locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
DEFAULT_TIMEFORMAT = "%Y-%m-%d %H:%M"
HUMAN_TIMEFORMAT = "%a %d/%m - %Hh%M"


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
    session = Session(start=start, end=end)
    db.session.add(session)
    db.session.commit()
    game.sessions.append(session)


def delete_game_session(session):
    """
    Delete a session for a game.
    """
    db.session.delete(session)
    db.session.commit()


def send_discord_embed(
    game,
    type="annonce",
    start=None,
    end=None,
    player=None,
    old_start=None,
    old_end=None,
):
    """
    Send Discord embed message for game.
    """
    if type == "annonce":
        print(game.__dict__)
        if game.type == "campaign":
            session_type = "Campagne"
        else:
            session_type = "OS"
        restriction = ":red_circle: 18+"
        if game.restriction == "all":
            restriction = ":green_circle: Tout public"
        elif game.restriction == "16+":
            restriction = ":yellow_circle: 16+"
        if game.restriction_tags == None:
            restriction_msg = f"{restriction}"
        else:
            restriction_msg = f"{restriction} {game.restriction_tags}"
        embed = {
            "title": game.name,
            "color": Game.COLORS[game.type],
            "fields": [
                {
                    "name": "MJ",
                    "value": game.gm.name,
                    "inline": True,
                },
                {"name": "Système", "value": game.system.name, "inline": True},
                {
                    "name": "Type de session",
                    "value": session_type,
                    "inline": True,
                },
                {
                    "name": "Date",
                    "value": game.date.strftime(HUMAN_TIMEFORMAT),
                    "inline": True,
                },
                {"name": "Durée", "value": game.length, "inline": True},
                {
                    "name": "Avertissement",
                    "value": restriction_msg,
                },
                {
                    "name": "Pour s'inscrire :",
                    "value": "https://questmaster.club-jdr.fr/annonces/{}/".format(
                        game.id
                    ),
                },
            ],
            "image": {
                "url": game.img,
            },
            "footer": {},
        }
        target = current_app.config["POSTS_CHANNEL_ID"]
    elif type == "add-session":
        embed = {
            "description": "<@&{}>\nVotre MJ a ajouté une nouvelle session : du **{}** au **{}**\n\nPour ne pas l'oublier pensez à l'ajouter à votre calendrier. Vous pouvez le faire facilement depuis [l'annonce sur QuestMaster](https://questmaster.club-jdr.fr/annonces/{}) en cliquant sur le bouton correspondant à la session.\nSi vous avez un empêchement prevenez votre MJ en avance.".format(
                game.role, start, end, game.id
            ),
            "title": "Nouvelle session prévue",
            "color": 5025616,  # green
        }
        target = game.channel
    elif type == "edit-session":
        embed = {
            "description": "<@&{}>\nVotre MJ a modifié la session ~~du {} au {}~~\nLa session a été décalée du **{}** au **{}**\nPensez à mettre à jour votre calendrier.".format(
                game.role, old_start, old_end, start, end
            ),
            "title": "Session modifiée",
            "color": 16771899,  # yellow
        }
        target = game.channel
    elif type == "del-session":
        embed = {
            "description": "<@&{}>\nVotre MJ a annulé la session du **{}** au **{}**\nPensez à l'enlever de votre calendrier.".format(
                game.role, start, end
            ),
            "title": "Session annulée",
            "color": 16007990,  # red
        }
        target = game.channel
    elif type == "register":
        embed = {
            "description": "<@{}> s'est inscrit. Bienvenue :wave: ".format(player),
            "title": "Nouvelle inscription",
            "color": 2201331,  # blue
        }
        target = game.channel
    if type == "annonce" and game.msg_id:
        response = bot.edit_embed_message(game.msg_id, embed, target)
    else:
        response = bot.send_embed_message(embed, target)
    return response["id"]


def set_default_search_parameters(status, game_type, restriction):
    if len(status) == 0:
        status = ["open"]
    if len(game_type) == 0:
        game_type = ["oneshot", "campaign"]
    if len(restriction) == 0:
        restriction = ["all", "16+", "18+"]
    return status, game_type, restriction


@app.route("/", methods=["GET"])
@app.route("/annonces/", methods=["GET"])
def search_games():
    """
    Search games.
    """
    status = []
    game_type = []
    restriction = []
    request_args = {}
    name = request.args.get("name", type=str)
    system = request.args.get("system", type=int)
    vtt = request.args.get("vtt", type=int)
    for s in ["open", "closed", "archived", "draft"]:
        if request.args.get(s, type=bool):
            status.append(s)
            request_args[s] = "on"
    for t in ["oneshot", "campaign"]:
        if request.args.get(t, type=bool):
            game_type.append(t)
            request_args[t] = "on"
    for r in ["all", "16+", "18+"]:
        if request.args.get(r, type=bool):
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
        queries.append(Game.name.ilike("%{}%".format(name)))
    if system:
        request_args["system"] = system
        queries.append(Game.system_id == system)
    if vtt:
        request_args["vtt"] = vtt
        queries.append(Game.vtt_id == vtt)
    page = request.args.get("page", 1, type=int)
    games = (
        Game.query.filter(*queries)
        .order_by(Game.date)
        .paginate(page=page, per_page=GAMES_PER_PAGE, error_out=False)
    )
    next_url = (
        url_for("search_games", page=games.next_num, **request_args)
        if games.has_next
        else None
    )
    prev_url = (
        url_for("search_games", page=games.prev_num, **request_args)
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
        systems=System.query.order_by("name").all(),
        vtts=Vtt.query.order_by("name").all(),
    )


@app.route("/annonces/<game_id>/", methods=["GET"])
def get_game_details(game_id) -> object:
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
        "game_details.html", payload=payload, game=game, is_player=is_player
    )


@app.route("/annonce/", methods=["GET"])
@login_required
def get_game_form() -> object:
    """
    Get form to create a new game.
    """
    payload = who()
    abort_if_not_gm(payload)
    return render_template(
        "game_form.html",
        payload=payload,
        systems=System.query.order_by("name").all(),
        vtts=Vtt.query.order_by("name").all(),
    )


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


@app.route("/annonce/", methods=["POST"])
@login_required
def create_game() -> object:
    """
    Create a new game and redirect to the game details.
    """
    payload = who()
    if not payload["is_gm"] and not payload["is_admin"]:
        abort(403)
    data = request.values.to_dict()
    gm_id = data["gm_id"]
    # Create the Game object
    new_game = Game(
        name=data["name"],
        type=data["type"],
        length=data["length"],
        gm_id=gm_id,
        system_id=data["system"],
        vtt_id=data["vtt"] if data["vtt"] != "" else None,
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
    new_game.party_selection = "party_selection" in data.keys()
    if "restriction_tags" in data.keys():
        restriction_tags = ""
        if data["restriction_tags"] != "":
            for item in yaml.safe_load(data["restriction_tags"]):
                restriction_tags += item["value"] + ", "
            new_game.restriction_tags = restriction_tags[:-2]
    if data["action"] == "open":
        create_game_session(
            new_game,
            new_game.date,
            new_game.date + timedelta(hours=float(new_game.session_length)),
        )
        # Create role and update object with role_id
        new_game.role = bot.create_role(
            role_name=data["name"],
            permissions=PLAYER_ROLE_PERMISSION,
            color=Game.COLORS[data["type"]],
        )["id"]
        # Create channel and update object with channel_id
        category = get_channel_category(new_game)
        new_game.channel = bot.create_channel(
            channel_name=re.sub("[^0-9a-zA-Z]+", "-", new_game.name.lower()),
            parent_id=category.id,
            role_id=new_game.role,
            gm_id=gm_id,
        )["id"]
        category.size = category.size + 1
    try:
        # Save Game in database
        db.session.add(new_game)
        db.session.commit()
        game = db.get_or_404(Game, new_game.id)
        game.msg_id = send_discord_embed(game)
        db.session.commit()
    except Exception as e:
        if data["action"] == "open":
            # Delete channel & role in case of error on post
            bot.delete_channel(new_game.channel)
            bot.delete_role(new_game.role)
        abort(500, e)
    return redirect(url_for("get_game_details", game_id=new_game.id))


@app.route("/annonces/<game_id>/editer/", methods=["GET"])
@login_required
def get_game_edit_form(game_id) -> object:
    """
    Get form to edit a game.
    """
    payload = who()
    game = get_game_if_authorized(payload, game_id)
    return render_template(
        "game_form.html",
        payload=payload,
        game=game,
        systems=System.query.order_by("name").all(),
        vtts=Vtt.query.order_by("name").all(),
    )


@app.route("/annonces/<game_id>/editer/", methods=["POST"])
@login_required
def edit_game(game_id) -> object:
    """
    Edit an existing game and redirect to the game details.
    """
    payload = who()
    game = get_game_if_authorized(payload, game_id)
    data = request.values.to_dict()
    gm_id = data["gm_id"]
    post = game.status == "draft" and data["action"] == "open"
    # Edit the Game object
    if game.status == "draft":
        game.name = data["name"]
        game.type = data["type"]
    game.system_id = data["system"]
    game.vtt_id = data["vtt"] if data["vtt"] != "" else None
    game.description = data["description"]
    game.date = datetime.strptime(data["date"], DEFAULT_TIMEFORMAT)
    game.length = data["length"]
    game.party_size = data["party_size"]
    game.party_selection = "party_selection" in data.keys()
    game.xp = data["xp"]
    game.session_length = data["session_length"]
    game.frequency = data.get("frequency") or None
    game.characters = data["characters"]
    game.classification = get_classification(data)
    game.ambience = get_ambience(data)
    game.complement = data.get("complement")
    game.img = data.get("img")
    game.restriction = data["restriction"]
    if "restriction_tags" in data.keys():
        restriction_tags = ""
        if data["restriction_tags"] != "":
            for item in yaml.safe_load(data["restriction_tags"]):
                restriction_tags += item["value"] + ", "
            game.restriction_tags = restriction_tags[:-2]
    if post:
        game.status = data["action"]
        create_game_session(
            game,
            game.date,
            game.date + timedelta(hours=float(game.session_length)),
        )
        # Create role and update object with role_id
        game.role = bot.create_role(
            role_name=data["name"],
            permissions=PLAYER_ROLE_PERMISSION,
            color=Game.COLORS[data["type"]],
        )["id"]
        # Create channel and update object with channel_id
        category = get_channel_category(game)
        game.channel = bot.create_channel(
            channel_name=re.sub("[^0-9a-zA-Z]+", "-", game.name.lower()),
            parent_id=category.id,
            role_id=game.role,
            gm_id=gm_id,
        )["id"]
        category.size = category.size + 1
    try:
        game.msg_id = send_discord_embed(game)
        # Save Game in database
        db.session.commit()
    except Exception as e:
        if post:
            # Delete channel & role in case of error on post
            bot.delete_channel(game.channel)
            bot.delete_role(game.role)
        abort(500, e)
    return redirect(url_for("get_game_details", game_id=game.id))


@app.route("/annonces/<game_id>/statut/", methods=["POST"])
@login_required
def change_game_status(game_id) -> object:
    """
    Change game status and redirect to the game details.
    """
    payload = who()
    game = get_game_if_authorized(payload, game_id)
    status = request.values.to_dict()["status"]
    game.status = status
    try:
        db.session.commit()
        if status == "archived":
            bot.delete_channel(game.channel)
            bot.delete_role(game.role)
    except Exception as e:
        abort(500, e)
    return redirect(url_for("get_game_details", game_id=game.id))


@app.route("/annonces/<game_id>/sessions/ajouter", methods=["POST"])
@login_required
def add_game_session(game_id) -> object:
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
    try:
        db.session.commit()
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
    return redirect(url_for("get_game_details", game_id=game_id))


@app.route("/annonces/<game_id>/sessions/<session_id>/editer", methods=["POST"])
@login_required
def edit_game_session(game_id, session_id) -> object:
    """
    Edit game session and redirect to the game details.
    """
    payload = who()
    game = get_game_if_authorized(payload, game_id)
    session = db.get_or_404(Session, session_id)
    old_start = session.start.strftime(HUMAN_TIMEFORMAT)
    old_end = session.end.strftime(HUMAN_TIMEFORMAT)
    session.start = request.values.to_dict()["date_start"]
    session.end = request.values.to_dict()["date_end"]
    if session.start > session.end:
        abort(500, "Impossible d'ajouter une session qui se termine avant de commencer")
    try:
        db.session.commit()
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
    return redirect(url_for("get_game_details", game_id=game_id))


@app.route("/annonces/<game_id>/sessions/<session_id>/supprimer", methods=["POST"])
@login_required
def remove_game_session(game_id, session_id) -> object:
    """
    Remove session from a game and redirect to the game details.
    """
    payload = who()
    game = get_game_if_authorized(payload, game_id)
    session = db.get_or_404(Session, session_id)
    start = session.start
    end = session.end
    delete_game_session(session)
    try:
        db.session.commit()
        send_discord_embed(
            game,
            type="del-session",
            start=start.strftime(HUMAN_TIMEFORMAT),
            end=end.strftime(HUMAN_TIMEFORMAT),
        )
    except Exception as e:
        abort(500, e)
    return redirect(url_for("get_game_details", game_id=game_id))


@app.route("/annonces/<game_id>/inscription/", methods=["POST"])
@login_required
def register_game(game_id) -> object:
    """
    Register a player to a game.
    """
    payload = who()
    game = db.get_or_404(Game, game_id)
    if game.status in ["closed", "archived"]:
        abort(500)
    if game.gm_id == payload["user_id"]:
        abort(403)
    game.players.append(db.get_or_404(User, payload["user_id"]))
    if len(game.players) == game.party_size and not game.party_selection:
        game.status = "closed"
    try:
        db.session.commit()
        bot.add_role_to_user(payload["user_id"], game.role)
        send_discord_embed(game, type="register", player=payload["user_id"])
    except Exception as e:
        abort(500, e)
    return redirect(url_for("get_game_details", game_id=game.id))


@app.route("/annonces/<game_id>/gerer/", methods=["POST"])
@login_required
def manage_game_registration(game_id) -> object:
    """
    Manage player registration for a game.
    """
    payload = who()
    game = db.get_or_404(Game, game_id)
    if game.status == "archived":
        abort(500)
    if game.gm_id != payload["user_id"] and not payload["is_admin"]:
        abort(403)
    data = request.values.to_dict()
    if data["action"] == "manage":
        for player in game.players:
            if player.id not in data:
                try:
                    game.players.remove(db.get_or_404(User, player.id))
                    db.session.commit()
                    bot.remove_role_from_user(player.id, game.role)
                except Exception as e:
                    abort(500, e)
    elif data["action"] == "add":
        uid = data["discord_id"]
        try:
            new_player = db.get_or_404(User, str(uid))
        except Exception:
            new_player = User(id=str(uid))
            db.session.add(new_player)
            db.session.commit()
            new_player.init_on_load()
        if not new_player.is_player:
            abort(500, "Cette personne n'est pas un·e joueur·euse sur le Discord")
        try:
            game.players.append(new_player)
            db.session.commit()
            bot.add_role_to_user(uid, game.role)
            send_discord_embed(game, type="register", player=uid)
        except Exception as e:
            abort(500, e)
    return redirect(url_for("get_game_details", game_id=game.id))


@app.route("/mes_annonces/", methods=["GET"])
@login_required
def my_gm_games() -> object:
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


@app.route("/mes_parties/", methods=["GET"])
@login_required
def my_games() -> object:
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
