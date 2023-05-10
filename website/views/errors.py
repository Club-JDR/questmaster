from flask import render_template
from website import app
from website.views.auth import who


@app.errorhandler(403)
def forbidden(e):
    return render_template("403.html", payload=who()), 403


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html", payload=who()), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("500.html", payload=who(), error=e), 500
