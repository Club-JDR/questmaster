from datetime import datetime

from website.api import create_api_blueprint
from website.utils.assets import asset, asset_css

from .admin import admin_bp
from .auth import auth_bp
from .demo import demo_bp
from .errors import error_bp
from .filters import duration_hours, format_datetime, hex_color, text_color
from .games import game_bp
from .misc import misc_bp
from .stats import stats_bp


def register_blueprints(app):
    app.register_blueprint(game_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(misc_bp)
    app.register_blueprint(error_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(demo_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(create_api_blueprint())


def register_filters(app):
    app.add_template_filter(format_datetime, name="format_datetime")
    app.add_template_filter(duration_hours, name="duration_hours")
    app.jinja_env.globals.update(
        hex_color=hex_color,
        text_color=text_color,
        asset=asset,
        asset_css=asset_css,
        now=lambda: datetime.now().isoformat(),
    )
