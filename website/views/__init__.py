from .games import game_bp
from .auth import auth_bp
from .health import health_bp
from .misc import misc_bp
from .errors import error_bp
from .stats import stats_bp
from .filters import format_datetime


def register_blueprints(app):
    app.register_blueprint(game_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(misc_bp)
    app.register_blueprint(error_bp)
    app.register_blueprint(stats_bp)


def register_filters(app):
    app.add_template_filter(format_datetime, name="format_datetime")
