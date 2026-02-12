from flask import Blueprint, jsonify, render_template, request

from config.constants import TEMPLATE_403, TEMPLATE_404, TEMPLATE_500
from website.exceptions import GameError, NotFoundError, UnauthorizedError, ValidationError

error_bp = Blueprint("errors", __name__)


def _wants_json():
    """Check if the client prefers a JSON response."""
    return (
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


@error_bp.app_errorhandler(403)
def forbidden(e):
    return render_template(TEMPLATE_403), 403


@error_bp.app_errorhandler(404)
def not_found(e):
    return render_template(TEMPLATE_404), 404


@error_bp.app_errorhandler(500)
def server_error(e):
    return render_template(TEMPLATE_500, error=e), 500
