from flask import (
    request,
    current_app,
    render_template,
    redirect,
    url_for,
    abort,
)
from website import app, db, bot
from website.models import Game, User, remove_archived
from website.views.auth import who, login_required
from datetime import datetime
import re, yaml


@app.route("/", methods=["GET"])
def open_games():
    """
    List all open games.
    """
    games = Game.query.filter_by(status="open").all()
    return render_template(
        "games.html", payload=who(), games=games, title="Les annonces en cours"
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
    return render_template("game_form.html", payload=payload)


@app.route("/annonce/", methods=["POST"])
@login_required
def create_game() -> object:
    """
    Create a new game and redirect to the game details.
    """
    payload = who()
    if not payload["is_gm"]:
        abort(403)
    else:
        try:
            data = request.values.to_dict()
            gm_id = data["gm_id"]
            # Create the Game object
            new_game = Game(
                gm_id=gm_id,
                name=data["name"],
                system=data["system"],
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
            if "pregen" in data.keys():
                new_game.pregen = True
            if "party_selection" in data.keys():
                new_game.party_selection = True
            if "img" in data.keys():
                new_game.img = data["img"]
            print(data)
            if data["action"] == "open":
                # Create role and update object with role_id
                permissions = "3072"  # view channel + send messages
                color = 0x0D6EFD  # blue
                if data["type"] == "oneshot":
                    color = 0x198754  # green
                new_game.role = bot.create_role(
                    role_name=data["name"], permissions=permissions, color=color
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
                # Send embed message to Discord
                restriction = ":red_cricle: 18+"
                if new_game.restriction == "all":
                    restriction = ":green_cricle: Tout public"
                elif new_game.restriction == "16+":
                    restriction = ":yellow_cricle: 16+"
                if new_game.restriction_tags == None:
                    restriction_msg = f"{new_game.restriction}"
                else:
                    restriction_msg = (
                        f"{new_game.restriction}: {new_game.restriction_tags}"
                    )
                embed = {
                    "title": new_game.name,
                    "color": color,
                    "description": new_game.description,
                    "fields": [
                        {
                            "name": "MJ",
                            "value": new_game.gm.name,
                            "inline": True,
                        },
                        {"name": "Système", "value": new_game.system, "inline": True},
                        {
                            "name": "Type de session",
                            "value": new_game.type,
                            "inline": True,
                        },
                        {
                            "name": "Date",
                            "value": new_game.date.strftime("%a %d/%m - %Hh%M"),
                            "inline": True,
                        },
                        {"name": "Durée", "value": new_game.length, "inline": True},
                        {
                            "name": "Avertissement",
                            "value": restriction_msg,
                        },
                        {
                            "name": "Pour s'inscrire :",
                            "value": "https://questmaster.club-jdr.fr/annonces/{}".format(
                                new_game.id
                            ),
                        },
                    ],
                    "image": {
                        "url": new_game.img,
                    },
                    "footer": {},
                }
                bot.send_embed_message(embed, current_app.config["POSTS_CHANNEL_ID"])
            return redirect(url_for("get_game_details", game_id=new_game.id))
        except Exception as e:
            # Delete channel & role in case of error
            bot.delete_channel(new_game.channel)
            bot.delete_role(new_game.role)
            abort(500, e)


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
        "games.html",
        payload=payload,
        games=games_as_gm,
        gm_only=True,
        title="Mes annonces",
    )


@app.route("/mes_parties/", methods=["GET"])
@login_required
def my_games() -> object:
    """
    List all of current user games
    """
    payload = who()
    try:
        user = db.session.get(User, payload["user_id"])
        games_as_player = user.games
        games_as_gm = user.games_gm
        games = games_as_player + games_as_gm
    except AttributeError:
        games = {}
    return render_template(
        "games.html",
        payload=payload,
        games=games,
        title="Mes parties en cours",
    )


"""
@app.route("/games/<game_id>", methods=["DELETE"])
def delete_game(game_id) -> object:
    game = Game.query.get(game_id)
    bot.delete_channel(game.channel)
    bot.delete_role(game.role)
    db.query.delete(game)
    db.query.commit()
    return jsonify({"game": int(game_id), "status": "deleted"})


@app.route("/games/<game_id>/register/<user_id>", methods=["POST"])
def register_player_for_game(game_id, user_id) -> object:
    game = Game.query.get(game_id)
    role_id = game.role
    bot.add_role_to_user(user_id, role_id)
    return jsonify({"user": user_id, "game": int(game_id), "status": "registered"})


@app.route("/games/<game_id>/unregister/<user_id>", methods=["DELETE"])
def unregister_player_for_game(game_id, user_id) -> object:
    game = Game.query.get(game_id)
    role_id = game.role
    bot.remove_role_from_user(user_id, role_id)
    return jsonify({"user": user_id, "game": int(game_id), "status": "unregistered"})

"""
