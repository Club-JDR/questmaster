from flask import jsonify, request
from api import app
from api import db
from api.models import Game


@app.route("/games/", methods=["GET", "POST"])
def games():
    if request.method == "POST":
        if request.is_json:
            data = request.get_json()
            new_game = Game(name=data["name"], type=data["type"])
            db.session.add(new_game)
            db.session.commit()
            return {"message": f"Game {new_game.id} has been created successfully."}
        else:
            return {"error": "The request payload is not in JSON format"}
    elif request.method == "GET":
        games = Game.query.all()
        results = [
            {
                "name": game.name,
                "type": game.type,
            }
            for game in games
        ]
        return {"count": len(results), "games": results}
