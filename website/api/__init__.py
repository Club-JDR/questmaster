"""QuestMaster REST API blueprint factory.

Creates the ``/api/v1/`` blueprint, registers sub-blueprints, and
exempts the API from CSRF protection (Bearer tokens are used instead
of cookies).

JSON error handling is centralized in ``website.views.errors`` and
automatically returns JSON for any request whose path starts with
``/api/``.
"""

from flask import Blueprint

from website.api.auth import auth_bp, exchange_token, refresh_token
from website.api.games import games_bp
from website.api.health import health_bp
from website.api.leaderboards import leaderboards_bp
from website.api.reference_data import reference_data_bp
from website.api.stats import stats_bp
from website.api.users import users_bp
from website.extensions import csrf


def create_api_blueprint() -> Blueprint:
    """Create and configure the top-level API blueprint.

    Returns:
        Configured Flask Blueprint mounted at ``/api/v1``.
    """
    api_bp = Blueprint("api", __name__, url_prefix="/api/v1")

    # Sub-blueprints
    api_bp.register_blueprint(health_bp)
    api_bp.register_blueprint(auth_bp)
    api_bp.register_blueprint(games_bp)
    api_bp.register_blueprint(users_bp)
    api_bp.register_blueprint(stats_bp)
    api_bp.register_blueprint(leaderboards_bp)
    api_bp.register_blueprint(reference_data_bp)

    # API uses Bearer tokens, not cookies — exempt POST views from CSRF.
    # Blueprint-level csrf.exempt() does not propagate to nested blueprints,
    # so we exempt each view function individually.
    csrf.exempt(exchange_token)
    csrf.exempt(refresh_token)

    return api_bp
