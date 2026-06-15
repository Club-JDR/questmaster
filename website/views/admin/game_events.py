"""Admin routes for the game event audit trail (read-only)."""

# Third-party imports
from flask import render_template

# Local imports
from website.services.game_event import GameEventService
from website.views.admin import admin_bp

game_event_service = GameEventService()


@admin_bp.route("/game-events/", methods=["GET"])
def list_game_events():
    """List the most recent game events (audit trail)."""
    events = game_event_service.get_recent(limit=200)
    return render_template("admin/game_events/list.html", events=events)
