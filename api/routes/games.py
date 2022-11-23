from flask import jsonify, request
from api import app
from api import db
from api.models import Game, User


@app.route("/games/", methods=["POST"])
def create_game():
    data = request.get_json()
    # Test if gm has the role or send unauthorized
    if User.query.get(data["gm"]).is_gm == False:
        return (
            jsonify({"error": "GM doesn't have the correct role on the server."}),
            401,
        )
    else:
        try:
            new_game = Game(name=data["name"], type=data["type"], gm=data["gm"])
            db.session.add(new_game)
            db.session.commit()
            return jsonify({"game": new_game.id, "status": "created"})
        except Exception as e:
            return jsonify({"error": e.args}), 500


@app.route("/games/", methods=["GET"])
def get_games():
    results = [game.to_json() for game in Game.query.all()]
    return jsonify({"count": len(results), "games": results})


@app.route("/games/<game_id>", methods=["GET"])
def get_game(game_id):
    return jsonify(Game.query.get(game_id).to_json())


@app.route("/games/<game_id>", methods=["DELETE"])
def delete_game(game_id):
    Game.query.filter_by(id=game_id).delete()
    db.session.commit()
    return jsonify({"game": int(game_id), "status": "deleted"})
