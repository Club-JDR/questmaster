from flask import jsonify, request
from api import app
from api import db
from api.models import User


@app.route("/users/", methods=["POST"])
def create_user():
    data = request.get_json()
    if User.query.get(data["id"]) == None:
        try:
            new_user = User(id=data["id"])
            db.session.add(new_user)
            db.session.commit()
            return jsonify({"user": new_user.id, "status": "created"})
        except Exception as e:
            return jsonify({"error": e.args}), 500
    else:
        return jsonify({"user": data["id"], "status": "exists"})


@app.route("/users/", methods=["GET"])
def get_users():
    results = [user.to_json() for user in User.query.all()]
    return jsonify({"count": len(results), "users": results})


@app.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    return jsonify(User.query.get(user_id).to_json())


@app.route("/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    User.query.filter_by(id=user_id).delete()
    db.session.commit()
    return jsonify({"user": user_id, "status": "deleted"})
