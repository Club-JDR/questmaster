from flask import (
    request,
    current_app,
    render_template,
    redirect,
    url_for,
    abort,
)
from website import app, db, bot
from website.models import Game, User, System, Vtt
from website.views.auth import who, login_required
from datetime import datetime
import re, yaml

GAMES_PER_PAGE = 12
GAME_LIST_TEMPLATE = "games.html"
PLAYER_ROLE_PERMISSION = "3072"  # view channel + send messages


def send_discord_embed(game):
    """
    Send Discord embed message for game.
    """
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
                "value": game.type,
                "inline": True,
            },
            {
                "name": "Date",
                "value": game.date.strftime("%a %d/%m - %Hh%M"),
                "inline": True,
            },
            {"name": "Durée", "value": game.length, "inline": True},
            {
                "name": "Avertissement",
                "value": restriction_msg,
            },
            {
                "name": "Pour s'inscrire :",
                "value": "https://questmaster.club-jdr.fr/annonces/{}/".format(game.id),
            },
        ],
        "image": {
            "url": game.img,
        },
        "footer": {},
    }
    bot.send_embed_message(embed, current_app.config["POSTS_CHANNEL_ID"])


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
    if name:
        request_args["name"] = name
    system = request.args.get("system", type=int)
    if system:
        request_args["system"] = system
    vtt = request.args.get("vtt", type=int)
    if vtt:
        request_args["vtt"] = vtt
    for s in ["open", "closed", "archived", "draft"]:
        if request.args.get(s, type=bool):
            status.append(s)
            request_args[s] = "on"
    # default status if unset
    if len(status) == 0:
        status = ["open"]
    for t in ["oneshot", "campaign"]:
        if request.args.get(t, type=bool):
            game_type.append(t)
            request_args[t] = "on"
    # default type if unset
    if len(game_type) == 0:
        game_type = ["oneshot", "campaign"]
    for r in ["all", "16+", "18+"]:
        if request.args.get(r, type=bool):
            restriction.append(r)
            request_args[r] = "on"
    # default restriction if unset
    if len(restriction) == 0:
        restriction = ["all", "16+", "18+"]
    queries = [
        Game.status.in_(status),
        Game.restriction.in_(restriction),
        Game.type.in_(game_type),
    ]
    if name:
        queries.append(Game.name.ilike("%{}%".format(name)))
    if system:
        queries.append(Game.system_id == system)
    if vtt:
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
    if not payload["is_gm"]:
        abort(403)
    return render_template(
        "game_form.html",
        payload=payload,
        systems=System.query.order_by("name").all(),
        vtts=Vtt.query.order_by("name").all(),
    )


@app.route("/annonce/", methods=["POST"])
@login_required
def create_game() -> object:
    """
    Create a new game and redirect to the game details.
    """
    payload = who()
    if not payload["is_gm"] and not payload["is_admin"]:
        abort(403)
    else:
        try:
            data = request.values.to_dict()
            gm_id = data["gm_id"]
            # Create the Game object
            new_game = Game(
                gm_id=gm_id,
                name=data["name"],
                system_id=data["system"],
                vtt_id=data["vtt"] if data["vtt"] != "" else None,
                description=data["description"],
                type=data["type"],
                date=datetime.strptime(data["date"], "%Y-%m-%d %H:%M"),
                length=data["length"],
                party_size=data["party_size"],
                restriction=data["restriction"],
                status=data["action"],
            )
            if "restriction_tags" in data.keys():
                restriction_tags = ""
                if data["restriction_tags"] != "":
                    for item in yaml.safe_load(data["restriction_tags"]):
                        restriction_tags += item["value"] + ", "
                    new_game.restriction_tags = restriction_tags[:-2]
            new_game.pregen = "pregen" in data.keys()
            new_game.party_selection = "party_selection" in data.keys()
            new_game.img = data.get("img", None)
            if data["action"] == "open":
                # Create role and update object with role_id
                new_game.role = bot.create_role(
                    role_name=data["name"],
                    permissions=PLAYER_ROLE_PERMISSION,
                    color=Game.COLORS[data["type"]],
                )["id"]
                # Create channel and update object with channel_id
                new_game.channel = bot.create_channel(
                    channel_name=re.sub("[^0-9a-zA-Z]+", "-", new_game.name.lower()),
                    parent_id=current_app.config.get("CATEGORIES_CHANNEL_ID"),
                    role_id=new_game.role,
                    gm_id=gm_id,
                )["id"]
            # Save Game in database
            db.session.add(new_game)
            db.session.commit()
            if data["action"] == "open":
                send_discord_embed(new_game)
            return redirect(url_for("get_game_details", game_id=new_game.id))
        except Exception as e:
            if data["action"] == "open":
                # Delete channel & role in case of error on post
                bot.delete_channel(new_game.channel)
                bot.delete_role(new_game.role)
            abort(500, e)


@app.route("/annonces/<game_id>/editer/", methods=["GET"])
@login_required
def get_game_edit_form(game_id) -> object:
    """
    Get form to edit a game.
    """
    payload = who()
    game = db.get_or_404(Game, game_id)
    if payload["user_id"] != game.gm.id and not payload["is_admin"]:
        abort(403)
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
    game = db.get_or_404(Game, game_id)
    if payload["user_id"] != game.gm.id and not payload["is_admin"]:
        abort(403)
    try:
        data = request.values.to_dict()
        gm_id = data["gm_id"]
        post = game.status == "draft" and data["action"] == "open"
        if post:
            game.status = data["action"]
        # Edit the Game object
        if game.status == "draft":
            game.name = data["name"]
            game.type = data["type"]
        game.system_id = data["system"]
        game.vtt_id = data["vtt"] if data["vtt"] != "" else None
        game.description = data["description"]
        game.date = datetime.strptime(data["date"], "%Y-%m-%d %H:%M")
        game.length = data["length"]
        game.party_size = data["party_size"]
        game.restriction = data["restriction"]
        if "restriction_tags" in data.keys():
            restriction_tags = ""
            if data["restriction_tags"] != "":
                for item in yaml.safe_load(data["restriction_tags"]):
                    restriction_tags += item["value"] + ", "
                game.restriction_tags = restriction_tags[:-2]
        game.pregen = "pregen" in data.keys()
        game.party_selection = "party_selection" in data.keys()
        game.img = data.get("img", None)
        if post:
            # Create role and update object with role_id
            game.role = bot.create_role(
                role_name=data["name"],
                permissions=PLAYER_ROLE_PERMISSION,
                color=Game.COLORS[data["type"]],
            )["id"]
            # Create channel and update object with channel_id
            game.channel = bot.create_channel(
                channel_name=re.sub("[^0-9a-zA-Z]+", "-", game.name.lower()),
                parent_id=current_app.config.get("CATEGORIES_CHANNEL_ID"),
                role_id=game.role,
                gm_id=gm_id,
            )["id"]
        # Save Game in database
        db.session.commit()
        if post:
            send_discord_embed(game)
        return redirect(url_for("get_game_details", game_id=game.id))
    except Exception as e:
        if post:
            # Delete channel & role in case of error on post
            bot.delete_channel(game.channel)
            bot.delete_role(game.role)
        abort(500, e)


@app.route("/annonces/<game_id>/statut/", methods=["POST"])
@login_required
def change_game_status(game_id) -> object:
    """
    Change game status and redirect to the game details.
    """
    payload = who()
    game = db.get_or_404(Game, game_id)
    if game.gm_id != payload["user_id"] and not payload["is_admin"]:
        abort(403)
    try:
        status = request.values.to_dict()["status"]
        game.status = status
        if status == "archived":
            bot.delete_channel(game.channel)
            bot.delete_role(game.role)
        db.session.commit()
        return redirect(url_for("get_game_details", game_id=game.id))
    except Exception as e:
        abort(500, e)


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
    game.players.append(User.query.get_or_404(payload["user_id"]))
    if len(game.players) == game.party_size and not game.party_selection:
        game.status = "closed"
    try:
        db.session.commit()
        bot.add_role_to_user(payload["user_id"], game.role)
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
    if not payload["is_gm"]:
        abort(403)
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
    List all of current user non archived games
    """
    payload = who()
    try:
        user = db.session.get(User, payload["user_id"])
        games_as_player = user.games
        games_as_gm = user.games_gm
        games = games_as_player + games_as_gm
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
