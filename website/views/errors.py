"""Error handlers for HTTP and domain-specific exceptions."""

import logging

from flask import Blueprint, jsonify, render_template, request

from config.constants import TEMPLATE_403, TEMPLATE_404, TEMPLATE_500
from website.exceptions import (
    DatabaseError,
    DiscordAPIError,
    GameError,
    NotFoundError,
    QuestMasterError,
    UnauthorizedError,
    ValidationError,
)

logger = logging.getLogger(__name__)

error_bp = Blueprint("errors", __name__)


def _wants_json():
    """Check if the client prefers a JSON response."""
    return request.path.startswith("/api/") or (
        request.accept_mimetypes.best_match(["application/json", "text/html"])
        == "application/json"
    )


@error_bp.app_errorhandler(NotFoundError)
def handle_not_found_error(e):
    """Handle NotFoundError exceptions."""
    if _wants_json():
        return jsonify(e.to_dict()), e.http_status
    return render_template(TEMPLATE_404), e.http_status


@error_bp.app_errorhandler(UnauthorizedError)
def handle_unauthorized_error(e):
    """Handle UnauthorizedError exceptions."""
    if _wants_json():
        return jsonify(e.to_dict()), e.http_status
    return render_template(TEMPLATE_403), e.http_status


@error_bp.app_errorhandler(ValidationError)
def handle_validation_error(e):
    """Handle ValidationError exceptions."""
    if _wants_json():
        return jsonify(e.to_dict()), e.http_status
    return render_template(TEMPLATE_500, error=e), e.http_status


@error_bp.app_errorhandler(GameError)
def handle_game_error(e):
    """Handle GameError exceptions (GameFull, GameClosed, etc.)."""
    if _wants_json():
        return jsonify(e.to_dict()), e.http_status
    return render_template(TEMPLATE_500, error=e), e.http_status


@error_bp.app_errorhandler(DiscordAPIError)
def handle_discord_api_error(e):
    """Handle Discord API errors."""
    logger.error("Discord API error: %s", e)
    if _wants_json():
        return jsonify({"error": "Discord API error", "code": "DISCORD_API_ERROR"}), 502
    return render_template(TEMPLATE_500, error=e), 502


@error_bp.app_errorhandler(DatabaseError)
def handle_database_error(e):
    """Handle database errors."""
    logger.error("Database error: %s", e)
    if _wants_json():
        return jsonify({"error": "Internal server error", "code": "DATABASE_ERROR"}), 500
    return render_template(TEMPLATE_500, error=e), 500


@error_bp.app_errorhandler(QuestMasterError)
def handle_questmaster_error(e):
    """Handle any remaining QuestMaster domain errors."""
    status = e.http_status or 500
    if _wants_json():
        return jsonify(e.to_dict()), status
    return render_template(TEMPLATE_500, error=e), status


@error_bp.app_errorhandler(403)
def forbidden(e):
    """Handle HTTP 403 Forbidden errors."""
    if _wants_json():
        return jsonify({"error": e.description, "code": "FORBIDDEN"}), 403
    return render_template(TEMPLATE_403), 403


@error_bp.app_errorhandler(405)
def method_not_allowed(e):
    """Handle HTTP 405 Method Not Allowed errors."""
    if _wants_json():
        return jsonify({"error": e.description, "code": "METHOD_NOT_ALLOWED"}), 405
    return render_template(TEMPLATE_500, error=e), 405


@error_bp.app_errorhandler(404)
def not_found(e):
    """Handle HTTP 404 Not Found errors."""
    if _wants_json():
        return jsonify({"error": e.description, "code": "NOT_FOUND"}), 404
    return render_template(TEMPLATE_404), 404


@error_bp.app_errorhandler(500)
def server_error(e):
    """Handle HTTP 500 Internal Server errors."""
    if _wants_json():
        return jsonify({"error": "Internal server error", "code": "INTERNAL_ERROR"}), 500
    return render_template(TEMPLATE_500, error=e), 500
