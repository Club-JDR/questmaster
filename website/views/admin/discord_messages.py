"""Admin routes for composing, sending and editing Discord messages."""

from flask import flash, redirect, render_template, request, session, url_for

from website.exceptions import DiscordAPIError, NotFoundError, ValidationError
from website.models import DiscordMessage
from website.services.discord_message import DiscordMessageService
from website.services.setting import SettingsService
from website.views.admin import admin_bp, get_list_params

discord_message_service = DiscordMessageService()
settings_service = SettingsService()


def _parse_color(raw: str | None) -> int | None:
    """Parse a hex color string (e.g. '#5865f2') into an integer.

    Args:
        raw: Raw color value from the form, or None.

    Returns:
        Integer color value, or None if absent/invalid.
    """
    if not raw:
        return None
    try:
        return int(raw.lstrip("#"), 16)
    except ValueError:
        return None


def _parse_message_form() -> dict:
    """Build a message field dict from the submitted compose/edit form.

    Returns:
        Dict with ``content``, ``title``, ``description``, ``color`` (int),
        ``footer`` and ``image_url`` keys.
    """
    return {
        "content": request.form.get("content", ""),
        "title": request.form.get("title", "").strip() or None,
        "description": request.form.get("description", "").strip() or None,
        "color": _parse_color(request.form.get("color")),
        "footer": request.form.get("footer", "").strip() or None,
        "image_url": request.form.get("image_url", "").strip() or None,
    }


def _form_view(data: dict, channel: str | None, msg_type: str) -> dict:
    """Shape parsed form data for re-rendering the template after a POST.

    Args:
        data: Parsed message fields (``color`` as int).
        channel: Selected channel ID.
        msg_type: Selected message type.

    Returns:
        Template-friendly form dict (``color`` rendered back to a hex string).
    """
    return {
        "channel": channel,
        "type": msg_type,
        "content": data.get("content") or "",
        "title": data.get("title") or "",
        "description": data.get("description") or "",
        "color": f"#{data['color']:06x}" if data.get("color") is not None else "",
        "footer": data.get("footer") or "",
        "image_url": data.get("image_url") or "",
    }


def _form_from_message(message: DiscordMessage) -> dict:
    """Shape a stored message for pre-filling the edit form.

    Args:
        message: The DiscordMessage being edited.

    Returns:
        Template-friendly form dict.
    """
    return {
        "channel": message.channel_id,
        "type": message.type,
        "content": message.content or "",
        "title": message.title or "",
        "description": message.description or "",
        "color": f"#{message.color:06x}" if message.color is not None else "",
        "footer": message.footer or "",
        "image_url": message.image_url or "",
    }


@admin_bp.route("/discord/", methods=["GET"])
def list_discord_messages():
    """List Discord messages sent through the admin panel."""
    page, search = get_list_params()
    pagination = discord_message_service.list_paginated(page=page, search=search)
    return render_template(
        "admin/discord/index.html",
        pagination=pagination,
        search=search,
        channels=settings_service.get_post_channels(),
    )


@admin_bp.route("/discord/<int:message_id>/delete", methods=["POST"])
def delete_discord_message(message_id):
    """Delete a sent message from Discord and remove its stored record."""
    try:
        discord_message_service.delete(message_id)
        flash("Message supprimé.", "success")
    except NotFoundError:
        flash("Message introuvable.", "danger")
    return redirect(url_for("admin.list_discord_messages"))


@admin_bp.route("/discord/channels/new", methods=["GET", "POST"])
def new_discord_channel():
    """Add a channel to the list of channels messages can be sent to."""
    if request.method == "POST":
        try:
            settings_service.add_post_channel(
                label=request.form.get("label", ""),
                channel_id=request.form.get("channel_id", ""),
                updated_by_id=session.get("user_id"),
            )
            flash("Salon ajouté.", "success")
            return redirect(url_for("admin.list_discord_messages"))
        except ValidationError as e:
            flash(str(e), "danger")

    return render_template("admin/discord/channel_form.html")


@admin_bp.route("/discord/channels/<channel_id>/delete", methods=["POST"])
def delete_discord_channel(channel_id):
    """Remove a channel from the list of channels messages can be sent to."""
    settings_service.remove_post_channel(channel_id, updated_by_id=session.get("user_id"))
    flash("Salon retiré.", "success")
    return redirect(url_for("admin.list_discord_messages"))


@admin_bp.route("/discord/compose", methods=["GET", "POST"])
def compose_discord_message():
    """Compose and send a new Discord message (plain or embed)."""
    channels = discord_message_service.get_post_channels()

    if request.method == "POST":
        channel_id = request.form.get("channel")
        msg_type = request.form.get("type", DiscordMessage.TYPE_PLAIN)
        data = _parse_message_form()
        try:
            discord_message_service.send(channel_id, msg_type, data)
            flash("Message envoyé.", "success")
            return redirect(url_for("admin.list_discord_messages"))
        except ValidationError as e:
            flash(str(e), "danger")
        except DiscordAPIError as e:
            flash(f"Erreur Discord : {e}", "danger")
        return render_template(
            "admin/discord/compose.html",
            channels=channels,
            message=None,
            form=_form_view(data, channel_id, msg_type),
        )

    return render_template(
        "admin/discord/compose.html",
        channels=channels,
        message=None,
        form={"channel": None, "type": DiscordMessage.TYPE_PLAIN},
    )


@admin_bp.route("/discord/<int:message_id>/edit", methods=["GET", "POST"])
def edit_discord_message(message_id):
    """Edit a previously-sent Discord message (channel and type are fixed)."""
    try:
        message = discord_message_service.get_by_id(message_id)
    except NotFoundError:
        flash("Message introuvable.", "danger")
        return redirect(url_for("admin.list_discord_messages"))

    if request.method == "POST":
        data = _parse_message_form()
        try:
            discord_message_service.edit(message_id, data)
            flash("Message mis à jour.", "success")
            return redirect(url_for("admin.list_discord_messages"))
        except ValidationError as e:
            flash(str(e), "danger")
        except DiscordAPIError as e:
            flash(f"Erreur Discord : {e}", "danger")
        return render_template(
            "admin/discord/compose.html",
            channels=discord_message_service.get_post_channels(),
            message=message,
            form=_form_view(data, message.channel_id, message.type),
        )

    return render_template(
        "admin/discord/compose.html",
        channels=discord_message_service.get_post_channels(),
        message=message,
        form=_form_from_message(message),
    )
