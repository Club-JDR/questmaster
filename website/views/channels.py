from flask import (
    request,
    render_template,
    redirect,
    url_for,
    abort,
)
from website import app, db
from website.models import Channel
from website.views.auth import who, login_required


@app.route("/admin/channels/", methods=["GET"])
@login_required
def get_form_channels():
    """
    Get admin Channel form.
    """
    payload = who()
    if not payload["is_admin"]:
        abort(403)
    c = Channel.query.all()
    return render_template(
        "admin.html", payload=who(), items=c, item="channels", title="Catégories des salons de parties"
    )


@app.route("/channels/", methods=["POST"])
@login_required
def create_channel() -> object:
    """
    Create a new channel and redirect to the channel list.
    """
    payload = who()
    if not payload["is_admin"]:
        abort(403)
    try:
        data = request.values.to_dict()
        c = Channel(id=data["channel_id"], type=data["channel_type"], size=data["channel_size"])
        # Save Channel in database
        db.session.add(c)
        db.session.commit()
        return redirect(url_for("get_form_channels"))
    except Exception as e:
        abort(500, e)


@app.route("/channels/<channel_id>/", methods=["POST"])
@login_required
def edit_channel(channel_id) -> object:
    """
    Edit an existing Channel category and redirect to the category list.
    """
    payload = who()
    if not payload["is_admin"]:
        abort(403)
    try:
        data = request.values.to_dict()
        c = db.get_or_404(Channel, channel_id)
        # Edit the Channel object
        c.type = data["channel_type"]
        c.size = data["channel_size"]
        # Save Channel in database
        db.session.commit()
        return redirect(url_for("get_form_channels"))
    except Exception as e:
        abort(500, e)
