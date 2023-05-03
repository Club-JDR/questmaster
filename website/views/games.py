from flask import jsonify, request, current_app, render_template, redirect, url_for
from website import app, db, bot
from website.models import Game, User, remove_archived
from website.views.auth import who, login_required
import re


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
    game = Game.query.get(game_id)
    is_player = False
    for player in game.players:
        if payload != {} and payload["user_id"] == player.id:
            is_player = True
    return render_template(
        "game_details.html", payload=payload, game=game, is_player=is_player
    )


@app.route("/annonce/", methods=["GET"])
def get_game_form() -> object:
    """
    Get form to create a new game.
    """
    payload = who()
    if not payload["is_gm"]:
        return redirect(url_for("open_games"))
    return render_template("game_form.html", payload=payload)

@app.route("/annonce/", methods=["POST"])
@login_required
def create_game() -> object:
    """
    Create a new game and redirect to the game details.
    """
    payload = who()
    if not payload["is_gm"]:
        return redirect(url_for("open_games"))
    return jsonify(request.values.to_dict())

@app.route("/mes_annonces/", methods=["GET"])
@login_required
def my_gm_games() -> object:
    """
    List all of games where current user is GM.
    """
    payload = who()
    if not payload["is_gm"]:
        return redirect(url_for("open_games"))
    try:
        games_as_gm = User.query.get(payload["user_id"]).games_gm
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
        games_as_player = User.query.get(payload["user_id"]).games
        games_as_gm = User.query.get(payload["user_id"]).games_gm
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
@app.route("/games/", methods=["POST"])
def create_game() -> object:
    data = request.get_json()
    # Test if gm has the role or send unauthorized
    if User.query.get(data["gm_id"]).is_gm == False:
        return (
            jsonify({"error": "GM doesn't have the correct role on the server."}),
            401,
        )
    else:
        try:
            # Create the Game object
            new_game = Game(
                name=data["name"],
                type=data["type"],
                length=data["length"],
                gm_id=data["gm_id"],
                system=data["system"],
                description=data["description"],
                restriction=data["restriction"],
                restriction_tags=data["restriction_tags"],
                party_size=data["party_size"],
                party_selection=data["party_selection"],
                pregen=data["pregen"],
            )
            # Create channel and update object with channel_id
            new_game.channel = bot.create_channel(
                channel_name=re.sub("[^0-9a-zA-Z]+", "-", new_game.name.lower()),
                parent_id=current_app.config.get("CATEGORIES_CHANNEL_ID"),
            )["id"]
            # Create role and update object with role_id
            permissions = "3072"
            color = 15844367
            new_game.role = bot.create_role(
                role_name=new_game.name, permissions=permissions, color=color
            )["id"]
            # Save Game in database
            db.query.add(new_game)
            db.query.commit()
            # Send embed message to Discord
            embed = {
                "title": new_game.name,
                "color": color,
                "fields": [
                    {
                        "name": "MJ",
                        "value": new_game.gm.serialize()["username"],
                        "inline": True,
                    },
                    {"name": "Système", "value": new_game.system, "inline": True},
                    {"name": "Description", "value": new_game.description},
                    {
                        "name": "Avertissement",
                        "value": f"{new_game.restriction}: {new_game.restriction_tags}",
                    },
                    {"name": "Type de query", "value": new_game.type, "inline": True},
                    {
                        "name": "Nombre de querys",
                        "value": new_game.length,
                        "inline": True,
                    },
                    {
                        "name": "Nombre de joueur·euses",
                        "value": f\"""{new_game.party_size}{" sur sélection" if new_game.party_selection else ""}\""",
                    },
                    {
                        "name": "Prétirés",
                        "value": f\"""{"Oui" if new_game.pregen else "Non"}\""",
                    },
                ],
                "footer": {},
            }
            bot.send_embed_message(embed, current_app.config["POSTS_CHANNEL_ID"])
            return jsonify({"game": new_game.id, "status": "created"})
        except Exception as e:
            return jsonify({"error": e.args}), 500


@app.route("/games/", methods=["GET"])
def get_games() -> object:
    results = [game.serialize() for game in Game.query.all()]
    return jsonify({"count": len(results), "games": results})


@app.route("/games/<game_id>/", methods=["GET"])
def get_game(game_id) -> object:
    return jsonify(Game.query.get(game_id).serialize())


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
