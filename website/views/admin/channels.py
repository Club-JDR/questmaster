"""Admin routes for managing Discord channel categories."""

# Third-party imports
from flask import flash, redirect, render_template, request, url_for

# Local imports
from config.constants import GAME_TYPES
from website.exceptions import NotFoundError, ValidationError
from website.services.channel import ChannelService
from website.views.admin import admin_bp

channel_service = ChannelService()


@admin_bp.route("/channels/", methods=["GET"])
def list_channels():
    """List all Discord channel categories."""
    channels = channel_service.get_all()
    return render_template("admin/channels/list.html", channels=channels)


@admin_bp.route("/channels/new", methods=["GET", "POST"])
def create_channel():
    """Create a new channel category."""
    if request.method == "POST":
        try:
            channel_service.create(
                channel_id=request.form.get("id", "").strip(),
                type=request.form.get("type"),
                size=int(request.form.get("size") or 0),
            )
            flash("Catégorie créée.", "success")
            return redirect(url_for("admin.list_channels"))
        except ValidationError as e:
            flash(str(e), "danger")

    return render_template("admin/channels/form.html", channel=None, game_types=GAME_TYPES)


@admin_bp.route("/channels/<channel_id>/edit", methods=["GET", "POST"])
def edit_channel(channel_id):
    """Edit an existing channel category."""
    try:
        channel = channel_service.get_by_id(channel_id)
    except NotFoundError:
        flash("Catégorie introuvable.", "danger")
        return redirect(url_for("admin.list_channels"))

    if request.method == "POST":
        channel_service.update(
            channel_id,
            {
                "type": request.form.get("type"),
                "size": int(request.form.get("size") or 0),
            },
        )
        flash("Catégorie mise à jour.", "success")
        return redirect(url_for("admin.list_channels"))

    return render_template("admin/channels/form.html", channel=channel, game_types=GAME_TYPES)


@admin_bp.route("/channels/<channel_id>/delete", methods=["POST"])
def delete_channel(channel_id):
    """Delete a channel category."""
    channel_service.delete(channel_id)
    flash("Catégorie supprimée.", "success")
    return redirect(url_for("admin.list_channels"))
