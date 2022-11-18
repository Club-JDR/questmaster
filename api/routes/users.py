from flask import jsonify, request
from api import app
from api import db
from api.models import User


@app.route("/users/", methods=["POST"])
def create_user():
    if request.is_json:
        data = request.get_json()
        try:
            new_user = User(id=data["id"])
            db.session.add(new_user)
            db.session.commit()
            return jsonify({"user": new_user.id, "status": "created"})
        except Exception as e:
            return jsonify({"error": e.args})
    else:
        return jsonify({"error": "The request payload is not in JSON format"})


@app.route("/users/", methods=["GET"])
def get_users():
    users = User.query.all()
    results = [
        user.to_json()
        for user in users
    ]
    return jsonify({"count": len(results), "users": results})


@app.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    user = User.query.get(user_id)
    return jsonify(user.to_json())


@app.route("/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    User.query.filter_by(id=user_id).delete()
    db.session.commit()
    return jsonify({"user": int(user_id), "status": "deleted"})
