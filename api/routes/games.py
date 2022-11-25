from flask import jsonify, request, current_app
from api import app, db, bot
from api.models import Game, User
import re


@app.route("/games/", methods=["POST"])
def create_game() -> object:
    """
    Endpoint to create a game.
    The gm id should point to a user who is gm otherwise the creation is stopped.
    """
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
            db.session.add(new_game)
            db.session.commit()
            # Send embed message to Discord
            embed = {
                "title": new_game.name,
                "color": color,
                "fields": [
                    {"name": "MJ", "value": new_game.gm.username, "inline": True},
                    {"name": "Système", "value": new_game.system, "inline": True},
                    {"name": "Description", "value": new_game.description},
                    {"name": "Avertissement", "value": f"{new_game.restriction}: {new_game.restriction_tags}"},
                    {"name": "Type de session", "value":  new_game.type, "inline": True},
                    {"name": "Nombre de sessions", "value": new_game.length, "inline": True},
                    {"name": "Nombre de joueur·euses", "value": f"""{new_game.party_size}{" sur sélection" if new_game.party_selection else ""}"""},
                    {"name": "Prétirés", "value": f"""{"Oui" if new_game.pregen else "Non"}"""},
                ],
                "footer": {},
            }
            bot.send_embed_message(embed, new_game.channel)
            return jsonify({"game": new_game.id, "status": "created"})
        except Exception as e:
            return jsonify({"error": e.args}), 500


@app.route("/games/", methods=["GET"])
def get_games() -> object:
    """
    Endpoint to list all games.
    """
    results = [game.serialize() for game in Game.query.all()]
    return jsonify({"count": len(results), "games": results})


@app.route("/games/<game_id>", methods=["GET"])
def get_game(game_id) -> object:
    """
    Endpoint to get details for a game by it's id.
    """
    return jsonify(Game.query.get(game_id).serialize())


@app.route("/games/<game_id>", methods=["DELETE"])
def delete_game(game_id) -> object:
    """
    Endpoint to delete a game.
    Deletes the game's channel and role from discord, then the game itself from the database.
    """
    game = Game.query.get(game_id)
    bot.delete_channel(game.channel)
    bot.delete_role(game.role)
    db.session.delete(game)
    db.session.commit()
    return jsonify({"game": int(game_id), "status": "deleted"})
