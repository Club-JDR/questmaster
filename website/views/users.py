from flask import jsonify, current_app, render_template
from website import app
from website import db
from website.models import User, Game, remove_archived
from website.views.auth import populate_session, login_required


@app.route("/mes_annonces/", methods=["GET"])
@login_required
def my_gm_games() -> object:
    """
    List all of games where current user is GM.
    """
    payload = populate_session()
    games_as_gm = User.query.get(payload["user_id"]).games_gm
    return render_template(
        "games.html", payload=payload, games=games_as_gm, gm_only=True
    )


@app.route("/mes_parties/", methods=["GET"])
@login_required
def my_games() -> object:
    """
    List all of current user games
    """
    payload = populate_session()
    games_as_player = User.query.get(payload["user_id"]).games
    games_as_gm = User.query.get(payload["user_id"]).games_gm
    return render_template(
        "games.html",
        payload=payload,
        games=remove_archived(games_as_player) + remove_archived(games_as_gm),
    )


@app.route("/users/", methods=["GET"])
def get_users() -> object:
    """
    Endpoint to list all users.
    """
    results = [user.serialize() for user in User.query.all()]
    return jsonify({"count": len(results), "users": results})


@app.route("/users/<user_id>", methods=["POST"])
def create_user(user_id) -> object:
    """
    Endpoint to create a user in the database if it doesn't already exist.
    """
    if User.query.get(user_id) == None:
        try:
            new_user = User(id=user_id)
            db.session.add(new_user)
            db.session.commit()
            return jsonify({"user": new_user.id, "status": "created"})
        except Exception as e:
            return jsonify({"error": e.args}), 500
    else:
        return jsonify({"user": user_id, "status": "exists"})


@app.route("/users/<user_id>", methods=["GET"])
def get_user(user_id) -> object:
    """
    Endpoint to get details for a user by it's id.
    """
    return jsonify(User.query.get(user_id).serialize())


@app.route("/users/<user_id>", methods=["DELETE"])
def delete_user(user_id) -> object:
    """
    Endpoint to delete a user from the database.
    """
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"user": user_id, "status": "deleted"})
