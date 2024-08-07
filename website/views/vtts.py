from flask import (
    request,
    render_template,
    redirect,
    url_for,
    abort,
)
from website import app, db
from website.models import Vtt
from website.views.auth import who, login_required


@app.route("/vtts/", methods=["GET"])
def list_vtts():
    """
    List all VTTs.
    """
    v = Vtt.query.all()
    return render_template(
        "list.html", payload=who(), items=v, item="vtts", title="Virtual TableTops"
    )


@app.route("/admin/vtts/", methods=["GET"])
@login_required
def get_form_vtts():
    """
    Get admin VTTs form.
    """
    payload = who()
    if not payload["is_admin"]:
        abort(403)
    v = Vtt.query.all()
    return render_template(
        "admin.html", payload=who(), items=v, item="vtts", title="Virtual TableTops"
    )


@app.route("/vtts/", methods=["POST"])
@login_required
def create_vtt() -> object:
    """
    Create a new system and redirect to the system list.
    """
    payload = who()
    if not payload["is_admin"]:
        abort(403)
    try:
        data = request.values.to_dict()
        v = Vtt(name=data["name"], icon=data["icon"])
        # Save System in database
        db.session.add(v)
        db.session.commit()
        return redirect(url_for("list_vtts"))
    except Exception as e:
        abort(500, e)


@app.route("/vtts/<vtt_id>/", methods=["POST"])
@login_required
def edit_vtt(vtt_id) -> object:
    """
    Edit an existing VTT and redirect to the VTT list.
    """
    payload = who()
    if not payload["is_admin"]:
        abort(403)
    try:
        data = request.values.to_dict()
        v = db.get_or_404(Vtt, vtt_id)
        # Edit the Game object
        v.name = data["name"]
        v.icon = data["icon"]
        # Save System in database
        db.session.commit()
        return redirect(url_for("list_vtts"))
    except Exception as e:
        abort(500, e)
