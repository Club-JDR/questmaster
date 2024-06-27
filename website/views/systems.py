from flask import (
    request,
    render_template,
    redirect,
    url_for,
    abort,
)
from website import app, db
from website.models import System
from website.views.auth import who, login_required


@app.route("/systemes/", methods=["GET"])
def list_systems():
    """
    List all VTTs.
    """
    s = System.query.all()
    return render_template(
        "list.html", payload=who(), items=s, item="systems", title="Systèmes"
    )


@app.route("/admin/systems/", methods=["GET"])
def get_form_systems():
    """
    Get admin systems form.
    """
    s = System.query.all()
    return render_template(
        "admin.html", payload=who(), items=s, item="systems", title="Systèmes"
    )


@app.route("/systems/", methods=["POST"])
@login_required
def create_system() -> object:
    """
    Create a new system and redirect to the system list.
    """
    payload = who()
    if not payload["is_admin"]:
        abort(403)
    else:
        try:
            data = request.values.to_dict()
            sys = System(name=data["name"], icon=data["icon"])
            # Save System in database
            db.session.add(sys)
            db.session.commit()
            return redirect(url_for("list_systems"))
        except Exception as e:
            abort(500, e)


@app.route("/systems/<system_id>/", methods=["POST"])
@login_required
def edit_system(system_id) -> object:
    """
    Edit an existing system and redirect to the system list.
    """
    payload = who()
    if not payload["is_admin"]:
        abort(403)
    else:
        try:
            data = request.values.to_dict()
            sys = db.get_or_404(System, system_id)
            # Edit the Game object
            sys.name = data["name"]
            sys.icon = data["icon"]
            # Save System in database
            db.session.commit()
            return redirect(url_for("list_systems"))
        except Exception as e:
            abort(500, e)
