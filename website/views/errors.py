from flask import render_template, Blueprint
from website.views.auth import who

error_bp = Blueprint("errors", __name__)


@error_bp.errorhandler(403)
def forbidden(e):
    return render_template("403.html", payload=who()), 403


@error_bp.errorhandler(404)
def not_found(e):
    return render_template("404.html", payload=who()), 404


@error_bp.errorhandler(500)
def server_error(e):
    return render_template("500.html", payload=who(), error=e), 500
