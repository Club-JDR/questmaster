"""Admin routes for the game event audit trail (read-only)."""

# Third-party imports
from flask import render_template

# Local imports
from config.constants import ADMIN_PAGE_SIZE
from website.services.game_event import GameEventService
from website.views.admin import admin_bp, get_list_params

game_event_service = GameEventService()


@admin_bp.route("/game-events/", methods=["GET"])
def list_game_events():
    """List the game event audit trail with search and pagination."""
    page, search = get_list_params()
    pagination = game_event_service.list_paginated(
        page=page, per_page=ADMIN_PAGE_SIZE, search=search
    )
    return render_template("admin/game_events/list.html", pagination=pagination, search=search)
