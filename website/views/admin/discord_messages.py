"""Admin routes for composing, sending and editing Discord messages."""

from flask import flash, redirect, render_template, request, session, url_for

from website.exceptions import DiscordAPIError, NotFoundError, ValidationError
from website.models import DiscordMessage
from website.services.discord_message import DiscordMessageService
from website.services.setting import SettingsService
from website.views.admin import admin_bp, get_list_params
from website.views.auth import require_permission

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


def _parse_buttons() -> list[dict]:
    """Build the list of link buttons from the parallel form arrays.

    Returns:
        A list of ``{"label", "url"}`` dicts, one per submitted button row.
    """
    labels = request.form.getlist("button_label")
    urls = request.form.getlist("button_url")
    count = max(len(labels), len(urls))
    return [
        {
            "label": (labels[i] if i < len(labels) else "").strip(),
            "url": (urls[i] if i < len(urls) else "").strip(),
        }
        for i in range(count)
    ]


def _parse_embeds() -> list[dict]:
    """Build the list of embeds from the parallel form arrays.

    Returns:
        A list of embed field dicts (``title``, ``description``, ``color`` as int,
        ``footer``, ``image_url``), one per submitted embed block.
    """
    titles = request.form.getlist("embed_title")
    descriptions = request.form.getlist("embed_description")
    colors = request.form.getlist("embed_color")
    footers = request.form.getlist("embed_footer")
    images = request.form.getlist("embed_image_url")
    count = max(len(titles), len(descriptions), len(colors), len(footers), len(images))

    def at(values: list[str], i: int) -> str:
        return values[i] if i < len(values) else ""

    return [
        {
            "title": at(titles, i).strip() or None,
            "description": at(descriptions, i).strip() or None,
            "color": _parse_color(at(colors, i)),
            "footer": at(footers, i).strip() or None,
            "image_url": at(images, i).strip() or None,
        }
        for i in range(count)
    ]


def _parse_message_form() -> dict:
    """Build a message field dict from the submitted compose/edit form.

    Returns:
        Dict with ``content`` (plain), an ``embeds`` list and a ``buttons`` list.
    """
    return {
        "content": request.form.get("content", ""),
        "embeds": _parse_embeds(),
        "buttons": _parse_buttons(),
    }


def _embed_to_form(embed: dict) -> dict:
    """Shape one embed dict for the template (``color`` as a hex string)."""
    return {
        "title": embed.get("title") or "",
        "description": embed.get("description") or "",
        "color": f"#{embed['color']:06x}" if embed.get("color") is not None else "",
        "footer": embed.get("footer") or "",
        "image_url": embed.get("image_url") or "",
    }


def _embeds_to_form(embeds: list[dict]) -> list[dict]:
    """Shape a list of embeds for the template, always yielding at least one block."""
    blocks = [_embed_to_form(embed) for embed in embeds or []]
    return blocks or [_embed_to_form({})]


def _form_view(data: dict, channel: str | None) -> dict:
    """Shape parsed form data for re-rendering the template after a POST.

    Args:
        data: Parsed message fields (``embeds`` colors as ints).
        channel: Selected channel ID.

    Returns:
        Template-friendly form dict (embed colors rendered back to hex strings).
    """
    return {
        "channel": channel,
        "content": data.get("content") or "",
        "embeds": _embeds_to_form(data.get("embeds")),
        "buttons": data.get("buttons") or [],
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
        "content": message.content or "",
        "embeds": _embeds_to_form(message.embed_list),
        "buttons": message.buttons or [],
    }


@admin_bp.route("/discord/", methods=["GET"])
@require_permission("discord.send")
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
@require_permission("discord.send")
def delete_discord_message(message_id):
    """Delete a sent message from Discord and remove its stored record."""
    try:
        discord_message_service.delete(message_id)
        flash("Message supprimé.", "success")
    except NotFoundError:
        flash("Message introuvable.", "danger")
    return redirect(url_for("admin.list_discord_messages"))


@admin_bp.route("/discord/channels/new", methods=["GET", "POST"])
@require_permission("discord.send")
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
@require_permission("discord.send")
def delete_discord_channel(channel_id):
    """Remove a channel from the list of channels messages can be sent to."""
    settings_service.remove_post_channel(channel_id, updated_by_id=session.get("user_id"))
    flash("Salon retiré.", "success")
    return redirect(url_for("admin.list_discord_messages"))


@admin_bp.route("/discord/compose", methods=["GET", "POST"])
@require_permission("discord.send")
def compose_discord_message():
    """Compose and send a new Discord message (content, embeds and/or buttons)."""
    channels = discord_message_service.get_post_channels()

    if request.method == "POST":
        channel_id = request.form.get("channel")
        data = _parse_message_form()
        try:
            discord_message_service.send(channel_id, data)
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
            form=_form_view(data, channel_id),
        )

    return render_template(
        "admin/discord/compose.html",
        channels=channels,
        message=None,
        form=_form_view({}, None),
    )


@admin_bp.route("/discord/<int:message_id>/edit", methods=["GET", "POST"])
@require_permission("discord.send")
def edit_discord_message(message_id):
    """Edit a previously-sent Discord message (its channel can be changed)."""
    try:
        message = discord_message_service.get_by_id(message_id)
    except NotFoundError:
        flash("Message introuvable.", "danger")
        return redirect(url_for("admin.list_discord_messages"))

    if request.method == "POST":
        channel_id = request.form.get("channel")
        data = _parse_message_form()
        try:
            discord_message_service.edit(message_id, channel_id, data)
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
            form=_form_view(data, channel_id),
        )

    return render_template(
        "admin/discord/compose.html",
        channels=discord_message_service.get_post_channels(),
        message=message,
        form=_form_from_message(message),
    )
