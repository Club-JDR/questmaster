"""Admin routes for managing Discord channel categories."""

# Third-party imports
from flask import flash, redirect, render_template, request, session, url_for

# Local imports
from config.constants import ADMIN_PAGE_SIZE, DISCORD_CATEGORY_CHANNEL_LIMIT, GAME_TYPES
from website.exceptions import DiscordAPIError, NotFoundError, ValidationError
from website.services.channel import ChannelService
from website.services.discord import DiscordService
from website.services.setting import SettingsService
from website.views.admin import admin_bp, get_list_params
from website.views.auth import require_permission

channel_service = ChannelService()
discord_service = DiscordService()
settings_service = SettingsService()


@admin_bp.route("/channels/", methods=["GET"])
@require_permission("channel.manage")
def list_channels():
    """List Discord channel categories with search and pagination."""
    page, search = get_list_params()
    pagination = channel_service.list_paginated(page=page, per_page=ADMIN_PAGE_SIZE, search=search)
    return render_template(
        "admin/channels/list.html",
        pagination=pagination,
        search=search,
        auto_threshold=settings_service.get_category_auto_threshold(),
        channel_limit=DISCORD_CATEGORY_CHANNEL_LIMIT,
        name_templates=settings_service.get_category_name_templates(),
        game_types=GAME_TYPES,
    )


@admin_bp.route("/channels/new", methods=["GET", "POST"])
@require_permission("channel.manage")
def create_channel():
    """Create a new Discord category and register it."""
    if request.method == "POST":
        try:
            channel_service.create_category(discord_service, type=request.form.get("type"))
            flash("Catégorie Discord créée.", "success")
            return redirect(url_for("admin.list_channels"))
        except ValidationError as e:
            flash(str(e), "danger")
        except DiscordAPIError:
            flash("La création de la catégorie Discord a échoué.", "danger")

    return render_template("admin/channels/form.html", channel=None, game_types=GAME_TYPES)


@admin_bp.route("/channels/reconcile", methods=["POST"])
@require_permission("channel.manage")
def reconcile_channels():
    """Re-count every category's channels on Discord and correct the stored sizes."""
    try:
        corrections = channel_service.reconcile_sizes(discord_service)
        if corrections:
            flash(f"{len(corrections)} catégorie(s) corrigée(s).", "success")
        else:
            flash("Toutes les catégories étaient déjà à jour.", "info")
    except DiscordAPIError:
        flash("La synchronisation avec Discord a échoué.", "danger")
    return redirect(url_for("admin.list_channels"))


@admin_bp.route("/channels/settings", methods=["POST"])
@require_permission("channel.manage")
def update_channel_settings():
    """Update the category auto-provision threshold and name templates."""
    user_id = session.get("user_id")
    try:
        settings_service.set_category_auto_threshold(
            request.form.get("auto_threshold", ""), updated_by_id=user_id
        )
        settings_service.set_category_name_templates(
            {t: request.form.get(f"template_{t}", "") for t in GAME_TYPES},
            updated_by_id=user_id,
        )
        flash("Paramètres des catégories mis à jour.", "success")
    except ValidationError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin.list_channels"))


@admin_bp.route("/channels/<channel_id>/edit", methods=["GET", "POST"])
@require_permission("channel.manage")
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
@require_permission("channel.manage")
def delete_channel(channel_id):
    """Delete a channel category."""
    channel_service.delete(channel_id)
    flash("Catégorie supprimée.", "success")
    return redirect(url_for("admin.list_channels"))
